import argparse
import os
import re
import subprocess


class VariableNotFound(Exception):
    """Raised when the template variable {{  }} is not found."""
    pass


def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)

    elif not arg.endswith("nomadtemplate"):
        parser.error("The file is not a .nomadtemplate!")
    else:
        return open(arg, 'r')  # return an open file handle


parser = argparse.ArgumentParser(description="Insert template snippets into nomad jobs")
parser.add_argument("filename", metavar="filename", type=lambda x: is_valid_file(parser, x),
                    help="The path to a nomad job template file")
parser.add_argument("--noplan", help="Just generates the nomad jobfile, does not run plan", action="store_true")
parser.add_argument("--run", "-r", help="Just generates the nomad jobfile, does not run plan", action="store_true")
args = parser.parse_args()

regex_matcher = r"{{ ([\w\-\.]+)\|*([\w\-\.]+)*\|*([\w\-\.]+)*\|*([\w\-\.]+)*\|*([\w\-\.]+)*\|*([\w\-\.]+)* }}"

with open(args.filename.name, "r") as templateFile:
    template = templateFile.read()
    matches = re.findall(regex_matcher, template)[0]
    service_name = matches[0]
    subdomain = matches[1] if matches[1] != "" else matches[0]
    if service_name is not None:
        if ".h" in subdomain:
            # Means we want this to be lan only
            replacement = f"""
            tags = [
            "traefik.enable=true",
            "traefik.http.middlewares.{service_name}-mid.headers.customresponseheaders.X-Job={service_name}",
            "traefik.http.middlewares.{service_name}-mid.headers.customresponseheaders.X-Task={service_name}",
            "traefik.http.middlewares.{service_name}-mid.headers.customresponseheaders.X-Service=http",
            "traefik.http.routers.registry-ui.rule=Host(`{subdomain}.jakecover.me`)",
            "traefik.http.services.{service_name}.loadbalancer.sticky=true",
            "traefik.tags=service",
            "traefik.frontend.rule=Host:{subdomain}.jakecover.me",
            "traefik.http.middlewares.{service_name}-mid-ipwhitelist.ipwhitelist.sourcerange=192.168.0.1/16",
            "traefik.http.routers.{service_name}.middlewares={service_name}-chain",
            "traefik.http.middlewares.{service_name}-chain.chain.middlewares={service_name}-mid,{service_name}-mid-ipwhitelist"
          ]
            """
        else:
            # This should be public
            replacement = f"""
                        tags = [
                        "traefik.enable=true",
                        "traefik.http.middlewares.{service_name}-mid.headers.customresponseheaders.X-Job={service_name}",
                        "traefik.http.middlewares.{service_name}-mid.headers.customresponseheaders.X-Task={service_name}",
                        "traefik.http.middlewares.{service_name}-mid.headers.customresponseheaders.X-Service=http",
                        "traefik.http.routers.registry-ui.rule=Host(`{subdomain}.jakecover.me`)",
                        "traefik.http.services.{service_name}.loadbalancer.sticky=true",
                        "traefik.tags=service",
                        "traefik.frontend.rule=Host:{subdomain}.jakecover.me",
                        "traefik.http.routers.{service_name}.middlewares={service_name}-mid",
                      ]
                        """
        output = re.sub(regex_matcher, replacement, template)
        print(service_name)
    else:
        raise VariableNotFound

    with open(os.path.splitext(args.filename.name)[0] + ".nomad", "w") as outputFile:
        outputFile.write(output)

    print("----------------------------\nPlanning Job\n----------------------------")

    if not args.noplan:
        plan_results = subprocess.run(
            ["nomad", "job", "plan", os.path.abspath(os.path.splitext(args.filename.name)[0] + ".nomad")],
            capture_output=True, text=True)
        if plan_results.returncode != 0:
            print(plan_results.stderr)
            raise RuntimeError("The planning failed! See results")
        print(plan_results.stdout)

        if args.run:
            print("----------------------------\nRunning Job\n----------------------------")
            command = None
            for line in plan_results.stdout.split("\n"):
                if re.match(r"nomad job run -check-index", line):
                    command = line
            if command is not None:
                run_results = subprocess.run(command)
                print(run_results.stdout)
                print(run_results.stderr)
            else:
                raise RuntimeError("Could not find a command in the plan response!")
