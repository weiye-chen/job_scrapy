import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# 设置页面
st.set_page_config(page_title="职业规划数据导航仪", layout="wide")


def load_data():
    conn = sqlite3.connect('career_market.db')
    df = pd.read_sql('SELECT * FROM jobs', conn)
    conn.close()
    return df


st.title("🚀 招聘市场数据洞察与职业规划")

df = load_data()

if df.empty:
    st.warning("数据库暂无数据，请先运行爬虫脚本入库。")
else:
    # --- 侧边栏过滤器 ---
    st.sidebar.header("数据筛选")
    selected_city = st.sidebar.multiselect("选择城市", options=df['city'].unique(), default=df['city'].unique())
    selected_edu = st.sidebar.multiselect("学历要求", options=df['education'].unique(),
                                          default=df['education'].unique())

    filtered_df = df[(df['city'].isin(selected_city)) & (df['education'].isin(selected_edu))]

    # --- 顶层核心指标 ---
    m1, m2, m3 = st.columns(3)
    m1.metric("样本总数", f"{len(filtered_df)} 份")
    avg_sal = filtered_df['salary_avg'].mean()
    m2.metric("市场平均月薪", f"￥{avg_sal:,.0f}" if not pd.isna(avg_sal) else "N/A")
    m3.metric("覆盖公司", f"{filtered_df['company'].nunique()} 家")

    # --- 可视化图表 ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💰 薪资分布情况")
        fig_salary = px.histogram(filtered_df, x="salary_avg", nbins=20,
                                  title="岗位薪资频率分布",
                                  labels={'salary_avg': '平均月薪'},
                                  color_discrete_sequence=['#636EFA'])
        st.plotly_chart(fig_salary, use_container_width=True)

    with col2:
        st.subheader("🎓 经验与薪资关系")
        fig_exp = px.box(filtered_df, x="experience", y="salary_avg",
                         title="不同工作经验的薪资区间",
                         points="all", color="experience")
        st.plotly_chart(fig_exp, use_container_width=True)

    # --- 职业规划核心：技能热力图 ---
    st.subheader("🛠️ 核心技能词云/频次统计")
    all_skills = ",".join(filtered_df['skills'].dropna()).split(",")
    skill_counts = pd.Series(all_skills).value_counts().head(15).reset_index()
    skill_counts.columns = ['技能', '出现次数']

    fig_skill = px.bar(skill_counts, x='出现次数', y='技能', orientation='h',
                       title="市场上最紧缺的技术栈 Top 15",
                       color='出现次数', color_continuous_scale='Viridis')
    st.plotly_chart(fig_skill, use_container_width=True)

    # --- 原始数据查看 ---
    with st.expander("查看详细数据表"):
        st.dataframe(filtered_df.drop(columns=['id']))