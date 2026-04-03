#!/usr/bin/env python3
"""
Python代码安全执行器
"""

import os
import sys
import json
import traceback
from typing import Dict, Any, Optional
import subprocess
import tempfile


class PythonExecutor:
    """Python代码执行器"""
    
    def __init__(self):
        self.timeout = 60  # 执行超时时间（秒）
        self.allowed_modules = [
            'pandas', 'numpy', 'matplotlib', 'plotly',
            'json', 'datetime', 'collections', 're',
            'math', 'statistics', 'scipy'
        ]
    
    def execute(self, 
                code: str,
                data_path: str = "",
                charts_dir: str = "",
                report_id: str = "") -> Dict:
        """执行Python代码"""
        
        # 安全检查
        self._validate_code(code)
        
        # 准备执行环境变量
        env_vars = {
            'data_path': data_path,
            'charts_dir': charts_dir,
            'report_id': report_id
        }
        
        # 构建完整代码
        full_code = self._prepare_code(code, env_vars)
        
        # 在临时文件中执行
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(full_code)
                temp_file = f.name
            
            # 执行
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=os.path.dirname(temp_file)
            )
            
            # 清理临时文件
            os.unlink(temp_file)
            
            # 解析结果
            if result.returncode == 0:
                # 执行成功，读取输出变量
                output = self._parse_output(result.stdout)
                return output
            else:
                # 执行失败
                return {
                    'success': False,
                    'error': result.stderr,
                    'analysis_text': f"执行错误: {result.stderr}",
                    'result_json': {},
                    'generated_charts': []
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': '执行超时',
                'analysis_text': '代码执行超时，请简化分析逻辑',
                'result_json': {},
                'generated_charts': []
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'analysis_text': f'执行异常: {str(e)}',
                'result_json': {},
                'generated_charts': []
            }
    
    def _validate_code(self, code: str) -> None:
        """代码安全检查"""
        
        forbidden_patterns = [
            'import os', 'import sys', 'import subprocess',
            'exec(', 'eval(', 'compile(',
            '__import__', 'open(', 'file(',
            'input(', 'raw_input(',
            'exit(', 'quit(',
            'globals()', 'locals()',
            'delattr', 'setattr', 'getattr',
            '__class__', '__bases__', '__subclasses__'
        ]
        
        for pattern in forbidden_patterns:
            if pattern in code:
                raise ValueError(f"代码包含禁止的内容: {pattern}")
    
    def _prepare_code(self, code: str, env_vars: Dict) -> str:
        """准备执行代码"""
        
        # 注入环境变量
        env_setup = f'''
import json

# 环境变量
data_path = "{env_vars.get('data_path', '')}"
charts_dir = "{env_vars.get('charts_dir', '')}"
report_id = "{env_vars.get('report_id', '')}"

# 输出变量初始化
analysis_text = ""
result_json = {}
generated_charts = []

'''
        
        # 添加结果收集代码
        result_collector = '''

# 收集结果
output_result = {
    "success": True,
    "analysis_text": analysis_text if isinstance(analysis_text, dict) else {"analysis": str(analysis_text)},
    "result_json": result_json,
    "generated_charts": generated_charts
}

print("===RESULT_START===")
print(json.dumps(output_result, ensure_ascii=False))
print("===RESULT_END===")
'''
        
        return env_setup + code + result_collector
    
    def _parse_output(self, stdout: str) -> Dict:
        """解析执行输出"""
        
        try:
            # 查找结果标记
            start_marker = "===RESULT_START==="
            end_marker = "===RESULT_END==="
            
            if start_marker in stdout and end_marker in stdout:
                start_idx = stdout.find(start_marker) + len(start_marker)
                end_idx = stdout.find(end_marker)
                result_json_str = stdout[start_idx:end_idx].strip()
                
                return json.loads(result_json_str)
            
            # 如果没有找到标记，返回默认结果
            return {
                'success': True,
                'analysis_text': {'output': stdout},
                'result_json': {},
                'generated_charts': []
            }
            
        except json.JSONDecodeError:
            return {
                'success': True,
                'analysis_text': {'raw_output': stdout},
                'result_json': {},
                'generated_charts': []
            }