""" Simple, fast and fun task runner, not unlike gulp / grunt (but fast, fun and zero dep)"""
import json
import sys
import subprocess, shutil
import os
import textwrap

PACKAGE = "supermoto"


def do_check(args):
    """ typecheck, lint etc goes here """
    c("mypy supermoto")


def do_black(args):
    """ do 'black' reformat of all code """
    c("py -m black supermoto")


def do_publish(args):
    if os.path.isdir("dist"):
        shutil.rmtree("dist")
    c("py setup.py sdist")
    c("twine upload dist/*")


def do_test(args):
    os.chdir("tests")
    c("pytest")


def default():
    show_help()


def do_docs(args):
    c("pdoc3 -o docs --force --html " + PACKAGE)
    c(f"mv docs/{PACKAGE}/* docs")
    os.rmdir("docs/" + PACKAGE)



# library functions here (or in own module, whatever, I don't care)


def run_node_bin(scriptname: str, arg: str):
    c(rf"node_modules\.bin\{scriptname} {arg}")


def c_spawn(cmd, cwd):
    print(">", cmd)
    subprocess.Popen(cmd, cwd=cwd, shell=True)


def copy_files(sources, destinations):
    """ copy each source to each destinatios """
    for src in sources:
        for dest in destinations:
            src = os.path.abspath(src)
            dest = os.path.abspath(dest)
            print("cp %s -> %s" % (src, dest))
            if not os.path.isdir(dest):
                print("File not found", dest)
                continue
            shutil.copy(src, dest)


def c(cmd):
    print(">", cmd)
    subprocess.check_call(cmd, shell=True)


def c_ignore(cmd):
    print(">", cmd)
    subprocess.call(cmd, shell=True)


def c_dir(cmd, dir):
    print("%s > %s" % (dir, cmd))
    subprocess.check_call(cmd, cwd=dir, shell=True)


# scaffolding starts. Do not edit below


def show_help():
    g = globals()
    print(
        "Command not found, try",
        sys.argv[0],
        " | ".join([n[3:] for n in g if n.startswith("do_")]),
        "| <command> -h",
    )


def main():
    """ Launcher. Do not modify """
    if len(sys.argv) < 2:
        default()
        return
    func = sys.argv[1]
    f = globals().get("do_" + func)
    if sys.argv[-1] == "-h":
        print(
            textwrap.dedent(f.__doc__).strip()
            if f.__doc__
            else "No documentation for this command"
        )
        return
    if not f:
        show_help()
        return
    f(sys.argv[2:])


if __name__ == "__main__":
    main()
