import argparse
import os
import re

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
args = parser.parse_args()

regex_matcher = r"{{ ([\w-]+) }}"

with open(args.filename.name, "r") as templateFile:
    template = templateFile.read()
    service_name = re.findall(regex_matcher, template)[0]
    if service_name is not None:
        replacement = f"""
        tags = [
        "traefik.enable=true",
        "traefik.http.middlewares.{service_name}-mid.headers.customresponseheaders.X-Job={service_name}",
        "traefik.http.middlewares.{service_name}.headers.customresponseheaders.X-Task={service_name}",
        "traefik.http.middlewares.{service_name}.headers.customresponseheaders.X-Service=http",
        "traefik.http.routers.registry-ui.rule=Host(`{service_name}.jakecover.me`)",
        "traefik.http.services.{service_name}.loadbalancer.sticky=true",
        "traefik.tags=service",
        "traefik.frontend.rule=Host:{service_name}.jakecover.me",
        "traefik.http.middlewares.{service_name}-mid-ipwhitelist.ipwhitelist.sourcerange=192.168.0.1/16",
        "traefik.http.routers.{service_name}.middlewares={service_name}-chain",
        "traefik.http.middlewares.{service_name}-chain.chain.middlewares={service_name}-mid,{service_name}-mid-ipwhitelist"
      ]
        """
        output = re.sub(regex_matcher, replacement, template)
        print(service_name)
    else:
        raise VariableNotFound

    with open(os.path.splitext(args.filename.name)[0] + ".nomad", "w") as outputFile:
        outputFile.write(output)
