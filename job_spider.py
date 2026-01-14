import time
import random
from DrissionPage import ChromiumPage
import db_handler as db
import json
import os
from itertools import product

def fetch_jd_content(page, job_id, security_id, lid):
    """
    进入职位详情页抓取 JD 全文
    """
    # 构造详情页 URL (Boss直聘的标准格式)
    detail_url = f'https://www.zhipin.com/job_detail/{job_id}.html?securityId={security_id}&lid={lid}'

    # 建议在新标签页打开，或者直接跳转
    page.get(detail_url)

    # 等待 JD 文本容器加载
    # Boss 的 JD 通常在 class 为 job-sec-text 的 div 中
    try:
        jd_ele = page.wait.ele_displayed('.job-sec-text', timeout=5)
        if jd_ele:
            return jd_ele.text
        return ""
    except:
        print(f"⚠️ 职位 {job_id} JD 抓取超时，可能需要手动验证")
        return ""


def process_list_and_jds(json_data, page):
    """
    处理列表数据，并循环抓取每一个职位的 JD
    """
    job_list = json_data.get('zpData', {}).get('jobList', [])

    for item in job_list:
        job_id = item.get('encryptJobId')
        security_id = item.get('securityId')
        lid = item.get('lid')
        job_name = item.get('jobName')

        print(f"🔍 正在深度抓取: {job_name}...")

        # --- 核心避坑逻辑：不要抓太快 ---
        time.sleep(random.uniform(5, 10))

        jd_text = fetch_jd_content(page, job_id, security_id, lid)

        if jd_text:
            # 将包含 JD 的完整数据存入数据库
            db.save_job_with_jd(item, jd_text)
            print(f"✅ 已成功存入 JD (长度: {len(jd_text)})")

        # 抓完一个回到列表页，或者保持在详情页继续下一个跳转
        # 建议直接 page.get 访问下一个详情页


if __name__ == '__main__':
    db.init_db()
    # 1. 读取配置文件
    config_path = 'config.json'
    if not os.path.exists(config_path):
        print(f"❌ 找不到配置文件: {config_path}")
        exit()

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 获取两个独立的列表
    queries = config.get('queries', [])
    cities = config.get('cities', [])
    interval = config.get('delay_between_tasks', 10)

    # 2. 启动浏览器
    boss_page = ChromiumPage()

    # 3. 使用 product 进行组合遍历 (Query x City)
    # product(['A', 'B'], [1, 2]) -> (A, 1), (A, 2), (B, 1), (B, 2)
    task_combinations = list(product(queries, cities))
    total_tasks = len(task_combinations)

    print(f"📊 已生成组合任务，共计 {total_tasks} 组。")

    for index, (query, city) in enumerate(task_combinations, 1):
        print(f"\n🚀 任务进度 [{index}/{total_tasks}]: {query} @ 城市代码:{city}")

        # 开启监听
        boss_page.listen.start('joblist.json')

        # 构造 URL
        target_url = f'https://www.zhipin.com/web/geek/job?query={query}&city={city}'
        boss_page.get(target_url)

        # 等待数据包
        res = boss_page.listen.wait(timeout=10)

        if res:
            data = res.response.body
            # 处理数据和抓取 JD
            process_list_and_jds(data, boss_page)
            print(f"✅ 完成抓取")
        else:
            print(f"⚠️ 响应超时，可能是因为 IP 限制或验证码。")
            # 建议：如果超时，可以在这里加一个 input("请处理验证码后按回车...")
            # 这样可以在不中断程序的情况下人工接入。

        # 任务间的休息
        if index < total_tasks:  # 最后一个任务完后不需要休息
            print(f"☕ 休息 {interval} 秒后切换组合...")
            time.sleep(interval)

    print("\n🎉 全量任务执行完毕！数据库已更新。")