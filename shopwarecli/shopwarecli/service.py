#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.. module:: TODO
   :platform: Unix
   :synopsis: TODO.

.. moduleauthor:: Aljosha Friemann <aljosha.friemann@gmail.com>

"""

import requests, json, os, logging

class Service:
    def __init__(self, host, user, password, version):
        if not host.startswith('http'):
            host = 'http://%s' % host

        self.host = host
        self.user = user
        self.password = password
        self.version = version

    def pretty(self, arg):
        try:
            arg = [ json.loads(a.to_json()) for a in arg ]
        except:
            pass

        if isinstance(arg, str):
            arg = json.loads(arg)

        return json.dumps(arg, indent=4, sort_keys=True)

    def request(self, method, path, accept = 200, data = None, files = None, headers = {}):
        URI = '{host}/{version}/{path}'.format(host=self.host, version=self.version, path=path)
        result = method(URI,
                        data=data,
                        files=files,
                        headers=headers,
                        auth=requests.auth.HTTPDigestAuth(self.user, self.password))

        if result.status_code != accept:
            message = 'failed to run %s on %s with returncode %s and message: "%s"' % (method.__name__, URI, result.status_code, result.text)
            if data is not None:
                message += '\ndata was: "%s"' % data
            if files is not None:
                message += '\nfiles was: %s' % files
            raise Exception(message)

        try:
            return result.json()
        except Exception as e:
            logging.error('json parsing failed, returning text: %s', e)
            return result.text

    def get(self, path, accept = 200, data = None, files = None, headers = {}):
        return self.request(requests.get, path, accept=accept, data=data, files=files, headers=headers)

    def post(self, path, accept = 200, data = None, files = None, headers = {}):
        return self.request(requests.post, path, accept=accept, data=data, files=files, headers=headers)

    def put(self, path, accept = 200, data = None, files = None, headers = {}):
        return self.request(requests.put, path, accept=accept, data=data, files=files, headers=headers)

    def delete(self, path, accept = 200, data = None, files = None, headers = {}):
        return self.request(requests.delete, path, accept=accept, data=data, files=files, headers=headers)

    def _format_(self, arg, pretty):
        if pretty:
            return self.pretty(arg)
        else:
            return arg

    def article_count(self):
        return int(self.get('articles?limit=0')['total'])

    def article(self, article_id, pretty):
        result = self.get('articles/{id}'.format(id=article_id))
        return self._format_(result, pretty)

    def articles(self, start, stop, limit, detail, pretty):
        if stop < 0:
            stop = self.article_count()

        articles = []

        logging.warn('requesting %s (start=%s, stop=%s) articles with limit %s', (stop - start), start, stop, limit)

        while start <= stop:
            result = self.get('articles?limit={limit}&start={start}'.format(limit=limit, start=start))['data']
            articles.extend(result)

            logging.debug('got %s articles', len(result))

            if limit == 0:
                break

            start += limit

        if detail:
            logging.warn('looking up detail information on %s articles', len(articles))

            detailed_articles = []

            for article in articles:
                detailed_articles.append(self.article(article['id'], pretty=False))

            return self._format_(detailed_articles, pretty)

        return self._format_(articles, pretty)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4 fenc=utf-8
