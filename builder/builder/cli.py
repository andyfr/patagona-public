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

def get_git_root(directory):
    cwd = os.getcwd()
    os.chdir(directory)

    proc = subprocess.Popen('git rev-parse --show-toplevel', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = proc.communicate()

    if proc.returncode != 0:
        raise Exception("not in a git tree: %s" % directory)

    os.chdir(cwd)

    return out.decode().strip()

def get_docker_namespace_from_git(git_root):
    git_dir = os.path.join(git_root, '.git')

    if os.path.exists(git_dir) and os.path.isdir(git_dir):
        proc = subprocess.Popen(
                ['git', '--git-dir=%s' % git_dir, '--work-tree=%s' % git_root, 'branch'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        out, err = proc.communicate()

        if err.decode() != '':
            log.error(err.decode())

        for line in out.decode().strip().split('\n'):
            if line.startswith('*'):
                return line

    return os.path.split(git_root)[1].strip()

def get_changed_dirs(git_root):
    cwd = os.getcwd()
    os.chdir(git_root)

    proc = subprocess.Popen(
            "git --no-pager diff --name-only HEAD^ | cut -d'/' -f1 | uniq",
            shell = True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

    out, err = proc.communicate()

    os.chdir(cwd)

    return out.decode().strip().split('\n')

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

def build_container(docker_repo, directory, test, compile, build, upload, version, name, namespace):
    # TODO split this up
    log.info('building docker image in %s', directory)

    cwd = os.getcwd()
    os.chdir(directory)

    for root, dirs, files in os.walk(directory):
        if test:
            if 'test' in files:
                if subprocess.call('./test') != 0:
                    log.error('failed to run tests for project: %s', name)
                    return False
            else:
                log.warning('no test script found for: %s', name)

        if compile:
            if 'compile' in files:
                if subprocess.call('./compile') != 0:
                    log.error('failed to build project: %s', name)
                    return False
            else:
                log.warning('no compile script found for: %s', name)

        if build:
            tag = '{docker}/{repo}/{project}'.format(
                    docker = docker_repo,
                    repo = namespace,
                    project = name)

            log.info('tagging image as {tag}:{version}'.format(tag = tag, version = version))

            if subprocess.call('docker build -t "{tag}:{version}" .'.format(tag = tag, version = version), shell=True) != 0:
                log.error('failed to build docker image for: %s', name)
                return False

            if upload:
                log.info('pushing image')

                if subprocess.call('docker push "{tag}"'.format(tag = tag), shell=True) != 0:
                    log.error('failed to push docker image (as %s) for: %s', version, name)
                    return False

                image_id = get_docker_images(tag, version)[0]['IMAGE']

                log.info('tagging image as {tag}:latest'.format(tag = tag, version = version))

                if subprocess.call('docker tag -f {image} "{tag}:latest"'.format(tag = tag, image = image_id), shell=True) != 0:
                    log.error('failed to tag docker image as latest for: %s', name)
                    return False

                log.info('pushing image')

                if subprocess.call('docker push "{tag}"'.format(tag = tag), shell=True) != 0:
                    log.error('failed to push docker image (as latest) for: %s', name)
                    return False
        break

    os.chdir(cwd)

    return True

def build_all_docker_images(docker_repo, directory, test, compile, build, upload, version, name, namespace):
    log.info('looking for dockerfiles in %s', directory)

    errors = 0

    for root, dirs, files in os.walk(directory):
        dirs[:] = [ d for d in dirs if d not in ['.git'] ]

        if not 'Dockerfile' in files:
            log.debug('no dockerfile found in %s', root)
            continue

        log.debug('found Docker file in %s', root)

        name = os.path.split(root)[1]

        log.info('using name "%s" for container in directory %s', name, root)

        if not build_container(docker_repo, root, test, compile, build, upload, version, name, namespace):
            log.error('failed to build container for %s with name %s and namespace %s', root, name, namespace)
            errors += 1

    return errors

@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('-r', '--docker-repo', required=True)
@click.option('-n', '--docker-namespace')
@click.option('-d', '--debug/--no-debug', default=False)
@click.option('-t', '--test/--no-test', default=True)
@click.option('-c', '--compile/--no-compile', default=True)
@click.option('-b', '--build/--no-build', default=True)
@click.option('-u', '--upload/--no-upload', default=True)
@click.option('-A', '--only-changed/--all', default=True)
@click.option('--version', required=True)
@click.option('--name')
@click.argument('path')
def cli(docker_repo, docker_namespace, debug, test, compile, build, upload, only_changed, version, name, path):
    loglevel = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=loglevel, format="%(asctime)s [%(levelname)s] - %(name)s: %(message)s")

    abs_path = os.path.abspath(path)

    if docker_namespace is not None:
        namespace = valid_docker_namespace(docker_namespace)
    else:
        git_root = get_git_root(abs_path)
        namespace = valid_docker_namespace(get_docker_namespace_from_git(git_root))

    log.debug('chose "%s" as namespace (docker_namespace was "%s", path was "%s")', namespace, docker_namespace, abs_path)

    errors = 0

    cwd = os.getcwd()

    if name is not None:
        log.info('building %s', abs_path)

        os.path.join(abs_path, "Dockerfile")
        if os.path.exists(os.path.join(abs_path, "Dockerfile")):
            if not build_container(docker_repo, abs_path, test, compile, build, upload, version, name, namespace):
                errors += 1
                log.error('failed to build container for %s with name %s and namespace %s', abs_path, name, namespace)
        else:
            log.error()
    elif only_changed:
        log.info('building changed directories in %s', abs_path)

        git_root = get_git_root(abs_path)

        changed_dirs = get_changed_dirs(git_root)

        for d in changed_dirs:
            if d is not None and d != '':
                errors += build_all_docker_images(docker_repo, os.path.join(git_root, d), test, compile, build, upload, version, name, namespace)
    else:
        log.info('building all directories in %s', abs_path)

        errors += build_all_docker_images(docker_repo, abs_path, test, compile, build, upload, version, name, namespace)

    # TODO remove created image

    exit(errors)

def run():
    cli()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4 fenc=utf-8
