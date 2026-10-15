"""最小修复：缓存 key 从只含 query 扩展为 (query, doc_ids, snapshot, k)。

原实现 challenge.Engine 的缓存 key 只用 query，导致不同资料版本(snapshot)、
不同文档范围(doc_ids)、不同返回数(k)共享同一条缓存，v2 请求命中 v1 的旧结论。
本文件只改 key 构造这一处，其余逻辑逐行保持一致，便于与 baseline 做同条件对照。
"""
import copy
import time
import uuid


class Engine:
    def __init__(self):
        self.cache = {}

    @staticmethod
    def _cache_key(request):
        return (
            request['query'].strip().lower(),
            tuple(request['doc_ids']),
            request['snapshot'],
            request['k'],
        )

    def evaluate(self, request, corpus, draft):
        started = time.perf_counter()
        key = self._cache_key(request)
        hit = key in self.cache
        if hit:
            result = copy.deepcopy(self.cache[key])
        else:
            terms = set(request['query'].strip().lower().split())
            ranked = sorted(corpus, key=lambda b: (-len(terms & set(b['tags'])), b['id']))
            selected = [b for b in ranked[:request['k']] if terms & set(b['tags'])]
            evidence = [b for b in selected if b['doc_id'] in request['doc_ids'] and b['snapshot'] == request['snapshot']]
            citations = draft['citations']
            valid = bool(citations) and set(citations).issubset({b['id'] for b in evidence})
            result = {'answer': draft['answer'], 'citations': citations, 'evidence': evidence,
                      'locator_status': 'valid' if valid else 'invalid',
                      'support_status': 'supported' if valid else 'not_checked',
                      'judgment_source': 'rule', 'status': 'ok'}
            self.cache[key] = copy.deepcopy(result)
        result.update(request_id=str(uuid.uuid4()), request=copy.deepcopy(request), cache_hit=hit,
                      elapsed_ms=(time.perf_counter()-started)*1000, run_kind='offline_replay')
        return result
