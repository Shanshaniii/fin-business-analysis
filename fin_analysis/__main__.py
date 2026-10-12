import argparse,json,html
from pathlib import Path
from http.server import BaseHTTPRequestHandler,HTTPServer
from .engine import run

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,default=Path(__file__).resolve().parents[1]/'data/synthetic.json');parser.add_argument('--serve',action='store_true');parser.add_argument('--port',type=int,default=8765);args=parser.parse_args()
 result=run(args.input)
 if not args.serve:print(json.dumps(result,ensure_ascii=False,indent=2));return
 class Handler(BaseHTTPRequestHandler):
  def do_GET(self):
   if self.path=='/api/results':body=json.dumps(result,ensure_ascii=False).encode();mime='application/json; charset=utf-8'
   elif self.path=='/':
    tables=[]
    for row in result['records']:
     cells=''.join('<tr><td>'+html.escape(k)+'</td><td>'+html.escape(m['display_value'] or '缺失')+'</td><td>'+html.escape(m['unit'])+'</td><td>'+html.escape(m['status'])+'</td></tr>' for k,m in row['metrics'].items())
     tables.append('<h2>'+html.escape(row['name']+' '+row['period'])+'</h2><table><tr><th>指标</th><th>数值</th><th>单位</th><th>状态</th></tr>'+cells+'</table>')
    body=('<!doctype html><html lang="zh"><meta charset="utf-8"><title>财务分析合成演示</title><style>body{font:16px system-ui;max-width:1000px;margin:40px auto;padding:0 24px}td,th{padding:10px 20px;border-bottom:1px solid #ddd;text-align:left}</style><h1>来源与口径约束的财务分析</h1><p>合成样例 · 非真实公司数据 · 模型未运行 · 经营原因与风险结论缺证</p>'+''.join(tables)+'<p>状态、真实质量及成本见仓库 docs/quality_and_cost.json。</p></html>').encode();mime='text/html; charset=utf-8'
   else:self.send_error(404);return
   self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 print('Demo: http://127.0.0.1:'+str(args.port),flush=True)
 HTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
if __name__=='__main__':main()
