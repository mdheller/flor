import setuptools
from setuptools.command.install import install
import io
import os
import conda.cli.python_api
import shutil
import sys
import subprocess

base_conda = 'base'
conda_flor_env = 'flor'
python_version = '3.7'


if len(sys.argv) > 1 and sys.argv[1] == 'install':

    print("The Flor installer needs to copy and transform an anaconda environment.\n"
          "This installer will take some time to complete.")

    while True:
        res = input("Continue with installation [Y/n]? ").strip().lower()
        if res == 'n':
            print("Exiting...")
            sys.exit(0)
        if res == 'y' or not res:
            break
        print("Invalid response: {}".format(res))

    base_conda = input("Enter the source anaconda environment [base]: ").strip() or base_conda
    python_version = input("Enter the Python version of the source anaconda environment [3.7]: ") or python_version
    conda_flor_env = input("Enter the name of the new anaconda environment [flor]: ").strip() or conda_flor_env


    FLOR_FUNC = """
    flor() {
            conda activate flor;
            pyflor $@;
            cd $(pwd);
            conda deactivate;
    }
    """

class PostInstallCommand(install):

    def run(self):

        install.run(self)

        from flor.complete_capture.walker import Walker

        # RUN script
        # subprocess.call(['./scripts/start'])
        conda.cli.python_api.run_command('create', '--name', conda_flor_env, '--clone', base_conda)

        raw_envs, _, _ = conda.cli.python_api.run_command('info', '--envs')
        raw_envs = raw_envs.split('\n')
        raw_envs = raw_envs[2:]

        env_path = None
        for raw_env in raw_envs:
            raw_env = raw_env.replace('*', '')
            name, path = raw_env.split()
            if name == conda_flor_env:
                env_path = path
                break
        assert env_path is not None

        env_path = os.path.join(env_path, 'lib', 'python'+python_version, 'site-packages')

        walker = Walker(env_path)
        walker.compile_tree()

        shutil.rmtree(env_path)
        shutil.move(walker.targetpath, env_path)

        print("Install succeeded.")

        print("Please append the following line to your shell configuration file:\n"
              "" + FLOR_FUNC)

with io.open("README.md", mode="r", encoding='utf-8') as fh:
    long_description = fh.read()

with open("requirements.txt", 'r') as f:
    requirements = f.read().split('\n')

setuptools.setup(
     name='pyflor',
     version='0.0.2a0',
     author="Rolando Garcia",
     author_email="rogarcia@berkeley.edu",
     description="A context-centric logger and automatic version controller",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://github.com/ucbrise/flor",
     packages=setuptools.find_packages(),
     install_requires = requirements,
     classifiers = [
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: Apache Software License",
         "Operating System :: OS Independent",
     ],
    entry_points={
        'console_scripts': [
            'pyflor = flor.__main__:main'
        ]
    },
    cmdclass={
        'install': PostInstallCommand
    }
 )
