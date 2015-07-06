#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. module:: TODO
   :platform: Unix
   :synopsis: TODO.

.. moduleauthor:: Aljosha Friemann <aljosha.friemann@gmail.com>

"""

import click, os, subprocess, logging, re

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

log = logging.getLogger('builder')

def tokenize(string):
    return re.split('\s+', string)

def valid_docker_namespace(string):
    # [a-z0-9-_]{4,30} docker v1.5.0
    return string.lstrip('*').split('/')[-1].strip().lower()[:30]

def get_docker_namespace_from_git(path):
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
                return valid_docker_namespace(line)

        return valid_docker_namespace(os.path.split(path)[1].strip())

def get_docker_images(name, tag = None):
    proc = subprocess.Popen(['docker', 'images'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if err.decode() != '':
        log.error(err.decode())

    lines = out.decode().strip().split('\n')

    keys = tokenize(lines[0])

    images = []

    for line in lines[1:]:
        if name in line:
            if tag and tag not in line:
                continue

            images.append(dict(zip(keys, tokenize(line))))

    return images

@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--version', required=True)
@click.option('-r', '--docker-repo', required=True)
@click.option('-n', '--docker-namespace')
@click.option('-d', '--debug/--no-debug', default=True)
@click.option('-t', '--test/--no-test', default=True)
@click.option('-c', '--compile/--no-compile', default=True)
@click.option('-b', '--build/--no-build', default=True)
@click.option('-u', '--upload/--no-upload', default=True)
@click.argument('path', default=os.getcwd())
def cli(docker_repo, docker_namespace, debug, test, compile, build, upload, version, path):
    loglevel = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=loglevel, format="%(asctime)s [%(levelname)s] - %(name)s: %(message)s")

    repo_path = os.path.abspath(path)

    namespace = get_docker_namespace_from_git(repo_path) if docker_namespace is None else valid_docker_namespace(docker_namespace)

    log.debug('chose "%s" as namespace (docker_namespace was "%s", path was "%s")', namespace, docker_namespace, path)

    errors = 0

    # TODO move this to class Builder

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [ d for d in dirs if d not in ['.git'] ]

        if not 'Dockerfile' in files:
            continue

        log.debug('found Docker file in %s', root)

        os.chdir(root)

        project_name = os.path.split(root)[1]

        if test:
            if 'test' in files:
                if subprocess.call('./test') != 0:
                    log.error('failed to run tests for project: %s', project_name)
                    errors += 1
                    continue
            else:
                log.warn('no test script found for: %s', project_name)

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

            if upload and subprocess.call('docker push "{tag}"'.format(tag = tag), shell=True) != 0:
                log.error('failed to push docker image (as %s) for: %s', version, project_name)
                errors += 1
                continue

            image_id = get_docker_images(tag, version)[0]['IMAGE']

            if subprocess.call('docker tag -f {image} "{tag}:latest"'.format(tag = tag, image = image_id), shell=True) != 0:
                log.error('failed to tag docker image as latest for: %s', project_name)
                errors += 1
                continue

            if subprocess.call('docker push "{tag}:latest"'.format(tag = tag), shell=True) != 0:
                log.error('failed to push docker image (as latest) for: %s', project_name)
                errors += 1
                continue

            # TODO remove created image

    exit(errors)

def run():
    cli()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4 fenc=utf-8
