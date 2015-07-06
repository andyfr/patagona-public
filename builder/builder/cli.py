#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. module:: TODO
   :platform: Unix
   :synopsis: TODO.

.. moduleauthor:: Aljosha Friemann <aljosha.friemann@gmail.com>

"""

import click, os, subprocess, logging

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

log = logging.getLogger('builder')

def get_docker_namespace(path):
    git_dir = os.path.join(path, '.git')

    if os.path.exists(git_dir) and os.path.isdir(git_dir):
        proc = subprocess.Popen(
                ['git', '--git-dir=%s' % git_dir, '--work-tree=%s' % path, 'branch'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        out, err = proc.communicate()

        if err.decode() != '':
            log.error(err.decode())

        for line in out.decode().strip().split('\n'):
            if line.startswith('*'):
                # [a-z0-9-_]{4,30} docker v1.5.0
                return line.lstrip('*').split('/')[-1].strip().lower()[:30]

        return os.path.split(path)[1].strip()

@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--version', required=True)
@click.option('-r', '--docker-repo', required=True)
@click.option('-t', '--test/--no-test', default=True)
@click.option('-c', '--compile/--no-compile', default=True)
@click.option('-b', '--build/--no-build', default=True)
@click.option('-u', '--upload/--no-upload', default=True)
@click.argument('path', default=os.getcwd())
def cli(docker_repo, test, compile, build, upload, version, path):
    repo_path = os.path.abspath(path)

    namespace = get_docker_namespace(repo_path)

    errors = 0

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [ d for d in dirs if d not in ['.git'] ]

        if not 'Dockerfile' in files:
            continue

        os.chdir(root)

        project_name = os.path.split(root)[1]

        if test:
            if 'test' in files:
                if subprocess.call('./test') != 0:
                    log.error('failed to run tests for project: %s', project_name)
                    errors += 1
                    continue
            else:
                log.warn('not test script found for: %s', project_name)

        if compile:
            if 'compile' in files:
                if subprocess.call('./compile') != 0:
                    log.error('failed to build project: %s', project_name)
                    errors += 1
                    continue
            else:
                log.warn('no compile script found for: %s', project_name)

        if build:
            tag = '{docker}/{repo}/{project}'.format(
                    docker = docker_repo,
                    repo = namespace,
                    project = project_name)

            if subprocess.call('docker build -t "{tag}:{version}" .'.format(tag = tag, version = version), shell=True) != 0:
                log.error('failed to build docker image for: %s', project_name)
                errors += 1
                continue

            if upload and subprocess.call('docker push "{repo}"'.format(repo = tag), shell=True) != 0:
                log.error('failed to push docker image for: %s', project_name)
                errors += 1
                continue

    exit(errors)

def run():
    cli()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4 fenc=utf-8