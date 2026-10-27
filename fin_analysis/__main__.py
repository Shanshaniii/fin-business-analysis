import argparse,json,html
from pathlib import Path
from http.server import BaseHTTPRequestHandler,HTTPServer
from .engine import run
from .answer_v2 import demo

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,default=Path(__file__).resolve().parents[1]/'data/synthetic.json');parser.add_argument('--serve',action='store_true');parser.add_argument('--port',type=int,default=8765);args=parser.parse_args()
 result=run(args.input)
 result['version']='2.0.0-demo'
 result['reference_contract_demo']=demo(result)
 if not args.serve:print(json.dumps(result,ensure_ascii=False,indent=2));return
 class Handler(BaseHTTPRequestHandler):
  def do_GET(self):
   if self.path=='/api/results':body=json.dumps(result,ensure_ascii=False).encode();mime='application/json; charset=utf-8'
   elif self.path=='/api/quality':body=(Path(__file__).resolve().parents[1]/'docs/quality_and_cost.json').read_bytes();mime='application/json; charset=utf-8'
   elif self.path=='/':
    tables=[]
    for row in result['records']:
     cells=''.join('<tr><td>'+html.escape(k)+'</td><td>'+html.escape(m['display_value'] or '缺失')+'</td><td>'+html.escape(m['unit'])+'</td><td>'+html.escape(m['status'])+'</td></tr>' for k,m in row['metrics'].items())
     tables.append('<h2>'+html.escape(row['name']+' '+row['period'])+'</h2><table><tr><th>指标</th><th>数值</th><th>单位</th><th>状态</th></tr>'+cells+'</table>')
    examples=''.join('<details><summary>'+html.escape(x['label'])+' · '+html.escape(x['outcome']['status'])+'</summary><pre>'+html.escape(json.dumps(x,ensure_ascii=False,indent=2))+'</pre></details>' for x in result['reference_contract_demo']['examples'])
    body=('<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>财务分析 V2.0 演示</title><style>body{font:16px system-ui;max-width:1000px;margin:40px auto;padding:0 24px;color:#192d38;background:#f7fafb}td,th{padding:10px 20px;border-bottom:1px solid #ddd;text-align:left}table{width:100%;background:white}details{padding:16px;margin:10px 0;background:white}pre{white-space:pre-wrap;overflow-wrap:anywhere}a{color:#126b75}</style><h1>财务分析 V2.0 演示</h1><p>合成样例 · 非真实公司数据 · 模型未运行 · 经营原因与风险结论缺证</p><h2>引用契约演示</h2><p>财务元数据来自程序登记；模型只能引用ID。合法结构不代表业务结论正确。</p>'+examples+''.join(tables)+'<h2>真实实验边界</h2><p>最新历史 Q25：9 次请求均后端终止，机械 final 2/4；D02 引用/期间失败，D04 输出截断。r2.3 的紧凑引用修复尚未真实复验。</p><p><a href="/api/quality">查看真实质量与成本 JSON</a> · <a href="/api/results">查看合成演示 JSON</a></p></html>').encode();mime='text/html; charset=utf-8'
   else:self.send_error(404);return
   self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 print('Demo: http://127.0.0.1:'+str(args.port),flush=True)
 HTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
if __name__=='__main__':main()
