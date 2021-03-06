#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. module:: TODO
   :synopsis: TODO.

.. moduleauthor:: Aljosha Friemann <aljosha.friemann@gmail.com>

"""

import click, logging

from . import service

log = logging.getLogger('shopwarecli')

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('-h', '--host', required=True)
@click.option('-u', '--user')
@click.option('-p', '--password')
@click.option('--pretty/--ugly', default=True)
@click.pass_context
def cli(ctx, host, user, password, pretty):
    """TODO: Docstring for shopwarecli."""
    ctx.obj['service'] = service.Service(host, user, password, version='api')
    ctx.obj['pretty'] = pretty

@cli.command()
@click.argument('article_id', nargs=-1)
@click.pass_context
def article(ctx, article_id):
    service = ctx.obj['service']

    for id in article_id:
        print(service.article(id, ctx.obj['pretty']))

@cli.command()
@click.option('-d', '--detail/--no-detail', default=False)
@click.option('-l', '--limit', default=500)
@click.option('--csv', multiple=True)
@click.argument('start', required=False, default=0)
@click.argument('stop', required=False, default=-1)
@click.pass_context
def articles(ctx, detail, limit, csv, start, stop):
    service = ctx.obj['service']

    articles = service.articles(start, stop, limit, detail, ctx.obj['pretty'])

    if csv is not None and csv != ():
        # import csv
        #
        # csv_file = open('output.csv', 'w')
        #
        # try:
        #     writer = csv.DictWriter(csv_file, ['gtin', 'name', 'price'])
        #     writer.writeheader()
        #
        #     counter = 0
        #
        #     for article in getArticles(args.url, USER, TOKEN, limit=100, get_all=True):
        #     # for article in getArticles(args.url, USER, TOKEN, limit=5):
        #         counter += 1
        #         gtin = article['mainDetail']['ean']
        #         name = article['name']
        #
        #         for price in article['mainDetail']['prices']:
        #             if price['customerGroupKey'] == 'EK':
        #                 price = price['price']
        #             else:
        #                 price = '!NO_EK_CG!'
        #
        #         article = {'gtin': gtin,
        #                    'name': name,
        #                    'price': price
        #                   }
        #
        #         print('%s: %s' % (counter, name))
        #
        #         writer.writerow(article)
        # finally:
        #     csv_file.close()
        raise NotImplementedError
    else:
        print(articles)

def run():
    logging.basicConfig(level=logging.WARN)
    cli(obj={})

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4 fenc=utf-8
