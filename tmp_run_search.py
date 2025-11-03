import json
from be.model.search import search_books
status, msg, res, total = search_books(q='python', fields=['title','content'], store_id=None, page=1, page_size=5)
print(json.dumps({'status': status, 'msg': msg, 'total': total, 'sample': res[:2]}, ensure_ascii=False, indent=2))
