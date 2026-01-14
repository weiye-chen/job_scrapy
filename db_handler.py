import sqlite3
import pandas as pd
import re
from datetime import datetime
import os

# 1. 数据库初始化
def init_db():
    if not os.path.exists('career_market.db'):
        conn = sqlite3.connect('career_market.db')
        cursor = conn.cursor()
        # 创建岗位表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name TEXT,
                salary_raw TEXT,
                salary_avg REAL,
                city TEXT,
                experience TEXT,
                education TEXT,
                company TEXT,
                skills TEXT,
                job_desc TEXT,
                scrape_date DATE,
                UNIQUE(job_name, company, city) -- 防止重复存储相同岗位
            )
        ''')
        conn.commit()
        conn.close()


# 2. 薪资清洗逻辑 (核心统计逻辑)
def clean_salary(salary_str):
    try:
        if not salary_str or '面议' in salary_str: return None
        nums = re.findall(r'\d+', salary_str)
        if len(nums) >= 2:
            low, high = int(nums[0]), int(nums[1])
            avg = (low + high) / 2
            if '薪' in salary_str and len(nums) >= 3:
                avg = (avg * int(nums[2])) / 12
            return avg * 1000  # 转化为元
        return None
    except:
        return None


# 3. 自动化存储函数
def save_to_db(json_data):
    conn = sqlite3.connect('career_market.db')
    cursor = conn.cursor()

    job_list = json_data.get('zpData', {}).get('jobList', [])
    count = 0

    for item in job_list:
        salary_str = item.get('salaryDesc')
        data = (
            item.get('jobName'),
            salary_str,
            clean_salary(salary_str),
            item.get('cityName'),
            item.get('jobExperience'),
            item.get('jobDegree'),
            item.get('brandName'),
            ",".join(item.get('skills', [])),
            datetime.now().strftime('%Y-%m-%d')
        )

        try:
            cursor.execute('''
                INSERT OR IGNORE INTO jobs 
                (job_name, salary_raw, salary_avg, city, experience, education, company, skills, scrape_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', data)
            count += cursor.rowcount
        except Exception as e:
            print(f"插入出错: {e}")

    conn.commit()
    conn.close()
    return count

def save_job_with_jd(item, jd_text):
    conn = sqlite3.connect('career_market.db')
    cursor = conn.cursor()

    # 这里复用之前的清洗逻辑
    avg_salary = clean_salary(item.get('salaryDesc'))

    data = (
        item.get('jobName'),
        item.get('salaryDesc'),
        avg_salary,
        item.get('cityName'),
        item.get('jobExperience'),
        item.get('jobDegree'),
        item.get('brandName'),
        ",".join(item.get('skills', [])),
        jd_text,  # 存入完整的 JD
        datetime.now().strftime('%Y-%m-%d')
    )

    cursor.execute('''
        INSERT OR REPLACE INTO jobs 
        (job_name, salary_raw, salary_avg, city, experience, education, company, skills, job_desc, scrape_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)

    conn.commit()
    conn.close()