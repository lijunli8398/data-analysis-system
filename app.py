#!/usr/bin/env python3
"""
数据分析问数系统 - 主入口（带项目管理）
"""

import streamlit as st
import sqlite3
import os
from datetime import datetime
from pathlib import Path

# 导入模块
from modules.report_generator import ReportGenerator
from modules.dashboard_generator import DashboardGenerator
from modules.question_engine import QuestionEngine
from modules.llm_client import LLMClient

# 配置
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "source"
OUTPUT_DIR = BASE_DIR / "output"

# 初始化数据库
def init_db():
    conn = sqlite3.connect(BASE_DIR / 'data.db')
    
    # 用户表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT
        )
    ''')
    
    # 项目表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT,
            description TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 报告表（增加project_id字段）
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            title TEXT,
            created_by TEXT,
            file_path TEXT,
            result_path TEXT,
            status TEXT DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 看板表（增加project_id字段）
    conn.execute('''
        CREATE TABLE IF NOT EXISTS dashboards (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            title TEXT,
            report_id TEXT,
            file_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 数据源表（增加project_id字段）
    conn.execute('''
        CREATE TABLE IF NOT EXISTS data_sources (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            name TEXT,
            file_path TEXT,
            uploaded_by TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 初始化默认用户
    try:
        conn.execute("INSERT INTO users VALUES ('admin', 'admin123', 'admin')")
        conn.execute("INSERT INTO users VALUES ('viewer', 'viewer123', 'viewer')")
    except sqlite3.IntegrityError:
        pass
    
    conn.commit()
    conn.close()

# 登录验证
def check_login(username, password):
    conn = sqlite3.connect(BASE_DIR / 'data.db')
    result = conn.execute(
        "SELECT role FROM users WHERE username=? AND password=?",
        (username, password)
    ).fetchone()
    conn.close()
    return result[0] if result else None

# 登录页面
def login_page():
    st.title("📊 数据分析问数系统")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("用户登录")
        
        username = st.text_input("用户名", key="login_username")
        password = st.text_input("密码", type="password", key="login_password")
        
        if st.button("登录", use_container_width=True):
            if username and password:
                role = check_login(username, password)
                if role:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.session_state['role'] = role
                    st.success(f"登录成功！角色：{role}")
                    st.rerun()
                else:
                    st.error("用户名或密码错误")
            else:
                st.warning("请输入用户名和密码")
        
        st.markdown("---")
        st.markdown("**默认账号：**")
        st.markdown("- 管理员：admin / admin123")
        st.markdown("- 查看者：viewer / viewer123")

# 项目管理页面（管理员）
def project_management_page():
    st.header("📁 项目管理")
    
    # 创建项目
    st.subheader("创建新项目")
    
    project_name = st.text_input("项目名称", key="project_name_input")
    project_desc = st.text_area("项目描述", height=100, key="project_desc_input")
    
    if st.button("创建项目", key="create_project_btn"):
        if project_name:
            project_id = datetime.now().strftime("%Y%m%d%H%M%S")
            
            conn = sqlite3.connect(BASE_DIR / 'data.db')
            conn.execute(
                "INSERT INTO projects VALUES (?, ?, ?, ?, ?)",
                (project_id, project_name, project_desc,
                 st.session_state['username'], datetime.now())
            )
            conn.commit()
            conn.close()
            
            st.success(f"项目 '{project_name}' 已创建")
            st.rerun()
        else:
            st.warning("请输入项目名称")
    
    # 项目列表
    st.subheader("项目列表")
    
    conn = sqlite3.connect(BASE_DIR / 'data.db')
    projects = conn.execute(
        "SELECT id, name, description, created_by, created_at FROM projects ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    
    if projects:
        for proj in projects:
            with st.expander(f"📂 {proj[1]}"):
                st.write(f"**项目ID:** {proj[0]}")
                st.write(f"**描述:** {proj[2] or '无'}")
                st.write(f"**创建者:** {proj[3]}")
                st.write(f"**创建时间:** {proj[4]}")
                
                # 统计该项目的报告和看板数量
                conn = sqlite3.connect(BASE_DIR / 'data.db')
                report_count = conn.execute(
                    "SELECT COUNT(*) FROM reports WHERE project_id=?", (proj[0],)
                ).fetchone()[0]
                dashboard_count = conn.execute(
                    "SELECT COUNT(*) FROM dashboards WHERE project_id=?", (proj[0],)
                ).fetchone()[0]
                conn.close()
                
                st.write(f"**报告数:** {report_count} | **看板数:** {dashboard_count}")
                
                # 删除按钮
                if st.button(f"删除项目", key=f"del_proj_{proj[0]}"):
                    conn = sqlite3.connect(BASE_DIR / 'data.db')
                    conn.execute("DELETE FROM projects WHERE id=?", (proj[0],))
                    conn.execute("DELETE FROM reports WHERE project_id=?", (proj[0],))
                    conn.execute("DELETE FROM dashboards WHERE project_id=?", (proj[0],))
                    conn.execute("DELETE FROM data_sources WHERE project_id=?", (proj[0],))
                    conn.commit()
                    conn.close()
                    st.success("项目已删除")
                    st.rerun()
                
                # 选择项目按钮
                if st.button(f"选择此项目", key=f"select_proj_{proj[0]}"):
                    st.session_state['current_project_id'] = proj[0]
                    st.session_state['current_project_name'] = proj[1]
                    st.success(f"已选择项目: {proj[1]}")
    else:
        st.info("暂无项目，请先创建项目")

# 数据管理页面（管理员）
def data_management_page():
    st.header("📁 数据源管理")
    
    # 显示当前选择的项目
    if 'current_project_id' not in st.session_state:
        st.warning("请先在【项目管理】中选择一个项目")
        return
    
    st.info(f"当前项目: {st.session_state.get('current_project_name', '未选择')}")
    
    # 上传数据
    st.subheader("上传数据文件")
    
    uploaded_file = st.file_uploader(
        "选择数据文件",
        type=['csv', 'xlsx', 'xls'],
        key="data_upload_file"
    )
    
    if uploaded_file:
        if st.button("保存数据源", key="save_data_btn"):
            file_id = datetime.now().strftime("%Y%m%d%H%M%S")
            file_path = DATA_DIR / f"{file_id}_{uploaded_file.name}"
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            conn = sqlite3.connect(BASE_DIR / 'data.db')
            conn.execute(
                "INSERT INTO data_sources VALUES (?, ?, ?, ?, ?, ?)",
                (file_id, st.session_state['current_project_id'],
                 uploaded_file.name, str(file_path),
                 st.session_state['username'], datetime.now())
            )
            conn.commit()
            conn.close()
            
            st.success(f"数据源已保存：{uploaded_file.name}")
            st.rerun()
    
    # 数据源列表（只显示当前项目的）
    st.subheader("当前项目的数据源")
    
    conn = sqlite3.connect(BASE_DIR / 'data.db')
    data_sources = conn.execute(
        "SELECT id, name, uploaded_by, uploaded_at FROM data_sources WHERE project_id=? ORDER BY uploaded_at DESC",
        (st.session_state['current_project_id'],)
    ).fetchall()
    conn.close()
    
    if data_sources:
        for ds in data_sources:
            with st.expander(f"📄 {ds[1]}"):
                st.write(f"ID: {ds[0]}")
                st.write(f"上传者: {ds[2]}")
                st.write(f"上传时间: {ds[3]}")
                
                if st.button(f"删除", key=f"del_data_{ds[0]}"):
                    conn = sqlite3.connect(BASE_DIR / 'data.db')
                    conn.execute("DELETE FROM data_sources WHERE id=?", (ds[0],))
                    conn.commit()
                    conn.close()
                    st.success("已删除")
                    st.rerun()
    else:
        st.info("当前项目暂无数据源")

# 报告生成页面（管理员）
def report_generation_page():
    st.header("📝 Word报告生成")
    
    if 'current_project_id' not in st.session_state:
        st.warning("请先在【项目管理】中选择一个项目")
        return
    
    st.info(f"当前项目: {st.session_state.get('current_project_name', '未选择')}")
    
    # 选择数据源
    conn = sqlite3.connect(BASE_DIR / 'data.db')
    data_sources = conn.execute(
        "SELECT id, name, file_path FROM data_sources WHERE project_id=? ORDER BY uploaded_at DESC",
        (st.session_state['current_project_id'],)
    ).fetchall()
    conn.close()
    
    if not data_sources:
        st.warning("请先在【数据管理】中上传数据源")
        return
    
    selected_data = st.selectbox(
        "选择数据源",
        data_sources,
        format_func=lambda x: x[1],
        key="report_data_source_select"
    )
    
    # 报告配置
    st.subheader("报告配置")
    
    report_title = st.text_input("报告标题", value="数据分析报告", key="report_title_input")
    
    analysis_prompt = st.text_area(
        "分析提示词（请填写分析需求、报告结构等）",
        value="",
        height=200,
        key="analysis_prompt_input",
        placeholder="例如：请分析销售数据，包含：\n1. 销售趋势分析\n2. 区域对比分析\n3. 产品排行分析\n\n输出结构：\n- 第一章：销售概述\n- 第二章：趋势分析（含图表）\n- 第三章：对比分析（含图表）\n- 第四章：结论与建议"
    )
    
    # 生成报告
    if st.button("🚀 生成报告", key="generate_report_btn"):
        if not analysis_prompt.strip():
            st.warning("请填写分析提示词")
            return
            
        with st.spinner("正在生成报告，请稍候..."):
            try:
                generator = ReportGenerator()
                
                result = generator.generate(
                    data_path=selected_data[2],
                    title=report_title,
                    prompt=analysis_prompt,
                    output_dir=OUTPUT_DIR
                )
                
                # 保存到数据库（绑定项目）
                conn = sqlite3.connect(BASE_DIR / 'data.db')
                conn.execute(
                    "INSERT INTO reports VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (result['report_id'], st.session_state['current_project_id'],
                     report_title, st.session_state['username'],
                     result['docx_path'], result['result_path'],
                     'completed', datetime.now())
                )
                conn.commit()
                conn.close()
                
                st.success("✅ 报告生成成功！")
                st.session_state['last_report_id'] = result['report_id']
                
                st.subheader("报告预览")
                st.write(f"报告ID: {result['report_id']}")
                
                with open(result['docx_path'], "rb") as f:
                    st.download_button(
                        "📥 下载Word报告",
                        f,
                        file_name=f"{report_title}.docx",
                        key=f"download_report_{result['report_id']}"
                    )
                
            except Exception as e:
                st.error(f"生成失败：{str(e)}")

# 看板生成页面（管理员）
def dashboard_generation_page():
    st.header("📊 仪表盘看板生成")
    
    if 'current_project_id' not in st.session_state:
        st.warning("请先在【项目管理】中选择一个项目")
        return
    
    st.info(f"当前项目: {st.session_state.get('current_project_name', '未选择')}")
    
    # 选择报告（只显示当前项目的）
    conn = sqlite3.connect(BASE_DIR / 'data.db')
    reports = conn.execute(
        "SELECT id, title, result_path FROM reports WHERE project_id=? AND status='completed' ORDER BY created_at DESC",
        (st.session_state['current_project_id'],)
    ).fetchall()
    conn.close()
    
    if not reports:
        st.warning("请先在【报告生成】中生成报告")
        return
    
    selected_report = st.selectbox(
        "选择关联报告",
        reports,
        format_func=lambda x: f"{x[1]} ({x[0]})",
        key="dashboard_report_select"
    )
    
    st.subheader("看板配置")
    
    dashboard_title = st.text_input("看板标题", value="数据分析看板", key="dashboard_title_input")
    
    dashboard_prompt = st.text_area(
        "看板配置提示词",
        value="""请根据数据生成以下图表：
1. 数据概览图表（饼图或柱状图）
2. 趋势变化图表（折线图）
3. 分组对比图表（柱状图）
4. 排名分析图表（条形图）""",
        height=150,
        key="dashboard_prompt_input"
    )
    
    if st.button("🚀 生成看板", key="generate_dashboard_btn"):
        with st.spinner("正在生成看板，请稍候..."):
            try:
                generator = DashboardGenerator()
                
                result = generator.generate(
                    result_path=selected_report[2],
                    title=dashboard_title,
                    prompt=dashboard_prompt,
                    output_dir=OUTPUT_DIR
                )
                
                # 保存到数据库（绑定项目）
                conn = sqlite3.connect(BASE_DIR / 'data.db')
                conn.execute(
                    "INSERT INTO dashboards VALUES (?, ?, ?, ?, ?, ?)",
                    (result['dashboard_id'], st.session_state['current_project_id'],
                     dashboard_title, selected_report[0], result['html_path'],
                     datetime.now())
                )
                conn.commit()
                conn.close()
                
                st.success("✅ 看板生成成功！")
                
                st.subheader("看板预览")
                with open(result['html_path'], "r") as f:
                    st.components.v1.html(f.read(), height=600, scrolling=True)
                
            except Exception as e:
                st.error(f"生成失败：{str(e)}")

# 报告查看页面
def report_view_page():
    st.header("📄 报告查看")
    
    # 项目筛选
    conn = sqlite3.connect(BASE_DIR / 'data.db')
    projects = conn.execute(
        "SELECT id, name FROM projects ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    
    if not projects:
        st.info("暂无项目")
        return
    
    selected_project = st.selectbox(
        "选择项目",
        projects,
        format_func=lambda x: x[1],
        key="report_view_project_select"
    )
    
    # 报告列表（按项目筛选）
    conn = sqlite3.connect(BASE_DIR / 'data.db')
    reports = conn.execute(
        "SELECT id, title, created_by, created_at, file_path FROM reports WHERE project_id=? AND status='completed' ORDER BY created_at DESC",
        (selected_project[0],)
    ).fetchall()
    conn.close()
    
    if not reports:
        st.info("该项目暂无报告")
        return
    
    selected_report = st.selectbox(
        "选择报告",
        reports,
        format_func=lambda x: f"{x[1]} - {x[3]}",
        key="report_view_report_select"
    )
    
    if selected_report:
        st.subheader(f"报告：{selected_report[1]}")
        st.write(f"创建者：{selected_report[2]}")
        st.write(f"创建时间：{selected_report[3]}")
        
        if os.path.exists(selected_report[4]):
            with open(selected_report[4], "rb") as f:
                st.download_button(
                    "📥 下载Word报告",
                    f,
                    file_name=f"{selected_report[1]}.docx",
                    key=f"download_view_report_{selected_report[0]}"
                )
            
            st.session_state['current_report_id'] = selected_report[0]
            st.session_state['current_report_title'] = selected_report[1]
            st.session_state['current_project_id'] = selected_project[0]
            st.session_state['current_project_name'] = selected_project[1]
            
            st.info(f"当前报告已设置为问数上下文")
        else:
            st.warning("报告文件不存在")

# 看板查看页面
def dashboard_view_page():
    st.header("📊 看板查看")
    
    conn = sqlite3.connect(BASE_DIR / 'data.db')
    projects = conn.execute(
        "SELECT id, name FROM projects ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    
    if not projects:
        st.info("暂无项目")
        return
    
    selected_project = st.selectbox(
        "选择项目",
        projects,
        format_func=lambda x: x[1],
        key="dashboard_view_project_select"
    )
    
    conn = sqlite3.connect(BASE_DIR / 'data.db')
    dashboards = conn.execute(
        "SELECT id, title, created_at, file_path FROM dashboards WHERE project_id=? ORDER BY created_at DESC",
        (selected_project[0],)
    ).fetchall()
    conn.close()
    
    if not dashboards:
        st.info("该项目暂无看板")
        return
    
    selected_dashboard = st.selectbox(
        "选择看板",
        dashboards,
        format_func=lambda x: f"{x[1]} - {x[2]}",
        key="dashboard_view_dashboard_select"
    )
    
    if selected_dashboard:
        st.subheader(f"看板：{selected_dashboard[1]}")
        st.write(f"创建时间：{selected_dashboard[2]}")
        
        if os.path.exists(selected_dashboard[3]):
            with open(selected_dashboard[3], "r") as f:
                st.components.v1.html(f.read(), height=600, scrolling=True)
            
            st.session_state['current_dashboard_id'] = selected_dashboard[0]
            st.session_state['current_dashboard_title'] = selected_dashboard[1]
            st.session_state['current_project_id'] = selected_project[0]
            st.session_state['current_project_name'] = selected_project[1]
            
            st.info(f"当前看板已设置为问数上下文")
        else:
            st.warning("看板文件不存在")

# 智能问数页面
def question_page():
    st.header("💬 智能问数")
    
    st.subheader("问数上下文")
    
    context_type = st.radio(
        "选择上下文来源",
        ["当前报告", "当前看板", "自由问数"],
        horizontal=True,
        key="question_context_type"
    )
    
    if context_type == "当前报告":
        if 'current_report_id' in st.session_state:
            st.info(f"当前报告：{st.session_state.get('current_report_title', '未选择')} | 项目：{st.session_state.get('current_project_name', '未选择')}")
        else:
            st.warning("请先在【报告查看】中选择一个报告")
    
    elif context_type == "当前看板":
        if 'current_dashboard_id' in st.session_state:
            st.info(f"当前看板：{st.session_state.get('current_dashboard_title', '未选择')} | 项目：{st.session_state.get('current_project_name', '未选择')}")
        else:
            st.warning("请先在【看板查看】中选择一个看板")
    
    st.subheader("开始问数")
    
    if 'question_history' not in st.session_state:
        st.session_state['question_history'] = []
    
    chat_container = st.container()
    with chat_container:
        for item in st.session_state['question_history']:
            with st.chat_message("user"):
                st.write(item['question'])
            with st.chat_message("assistant"):
                st.write(item['answer'])
                if item.get('chart'):
                    st.components.v1.html(item['chart'], height=300)
    
    question = st.chat_input("输入问题...")
    
    if question:
        with st.chat_message("user"):
            st.write(question)
        
        context = get_question_context(context_type)
        
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                try:
                    engine = QuestionEngine()
                    response = engine.ask(question, context)
                    
                    st.write(response['answer'])
                    
                    if response.get('chart'):
                        st.components.v1.html(response['chart'], height=300)
                    
                    st.session_state['question_history'].append({
                        'question': question,
                        'answer': response['answer'],
                        'chart': response.get('chart')
                    })
                    
                except Exception as e:
                    st.error(f"问数失败：{str(e)}")

# 获取问数上下文
def get_question_context(context_type):
    conn = sqlite3.connect(BASE_DIR / 'data.db')
    context = {'type': context_type}
    
    # 添加项目信息
    if 'current_project_id' in st.session_state:
        context['project_id'] = st.session_state['current_project_id']
        context['project_name'] = st.session_state['current_project_name']
    
    if context_type == "当前报告":
        if 'current_report_id' in st.session_state:
            report = conn.execute(
                "SELECT id, title, file_path, result_path FROM reports WHERE id=?",
                (st.session_state['current_report_id'],)
            ).fetchone()
            if report:
                context['report_id'] = report[0]
                context['report_title'] = report[1]
                context['report_path'] = report[2]
                context['result_path'] = report[3]
    
    elif context_type == "当前看板":
        if 'current_dashboard_id' in st.session_state:
            dashboard = conn.execute(
                "SELECT id, title, file_path FROM dashboards WHERE id=?",
                (st.session_state['current_dashboard_id'],)
            ).fetchone()
            if dashboard:
                context['dashboard_id'] = dashboard[0]
                context['dashboard_title'] = dashboard[1]
                context['dashboard_path'] = dashboard[2]
    
    conn.close()
    return context

# 用户管理页面
def user_management_page():
    st.header("👥 用户管理")
    
    st.subheader("添加新用户")
    
    new_username = st.text_input("用户名", key="new_username_input")
    new_password = st.text_input("密码", key="new_password_input")
    new_role = st.selectbox("角色", ["viewer", "admin"], key="new_role_select")
    
    if st.button("添加用户", key="add_user_btn"):
        if new_username and new_password:
            conn = sqlite3.connect(BASE_DIR / 'data.db')
            try:
                conn.execute(
                    "INSERT INTO users VALUES (?, ?, ?)",
                    (new_username, new_password, new_role)
                )
                conn.commit()
                st.success(f"用户 {new_username} 已添加")
            except sqlite3.IntegrityError:
                st.error("用户名已存在")
            conn.close()
            st.rerun()
        else:
            st.warning("请填写完整信息")
    
    st.subheader("现有用户")
    
    conn = sqlite3.connect(BASE_DIR / 'data.db')
    users = conn.execute("SELECT username, role FROM users").fetchall()
    conn.close()
    
    for user in users:
        st.write(f"- {user[0]} ({user[1]})")

# 主函数
def main():
    init_db()
    st.set_page_config(
        page_title="数据分析问数系统",
        page_icon="📊",
        layout="wide"
    )
    
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        login_page()
        return
    
    with st.sidebar:
        st.title("📊 数据分析问数系统")
        st.markdown("---")
        st.write(f"**用户：** {st.session_state['username']}")
        st.write(f"**角色：** {st.session_state['role']}")
        
        if 'current_project_name' in st.session_state:
            st.write(f"**当前项目：** {st.session_state['current_project_name']}")
        
        if st.button("退出登录", key="logout_btn"):
            st.session_state['logged_in'] = False
            st.session_state.clear()
            st.rerun()
    
    role = st.session_state['role']
    
    if role == 'admin':
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📁 项目管理", "📂 数据管理", "📝 报告生成", "📊 看板生成",
            "📄 报告查看", "📊 看板查看", "💬 智能问数"
        ])
        
        with tab1:
            project_management_page()
        with tab2:
            data_management_page()
        with tab3:
            report_generation_page()
        with tab4:
            dashboard_generation_page()
        with tab5:
            report_view_page()
        with tab6:
            dashboard_view_page()
        with tab7:
            question_page()
        
        with st.sidebar:
            st.markdown("---")
            if st.button("👥 用户管理", key="user_mgmt_btn"):
                st.session_state['show_user_mgmt'] = True
        
        if st.session_state.get('show_user_mgmt'):
            user_management_page()
    
    else:
        tab1, tab2, tab3 = st.tabs([
            "📄 报告查看", "📊 看板查看", "💬 智能问数"
        ])
        
        with tab1:
            report_view_page()
        with tab2:
            dashboard_view_page()
        with tab3:
            question_page()

if __name__ == "__main__":
    main()