import os
import sys
import requests
import frontmatter
from datetime import datetime
import subprocess
import time

def request_ai(api_key: str, user_prompt: str, system_prompt: str = None):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    messages = []
    if (system_prompt != None):
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    data = {
        "model": "qwen/qwen3-coder:free",  # or any other model like mistralai/mixtral
        "messages": messages
    }
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content'].strip()

def generate_title(keyword: str, api_key: str) -> str:
    system_prompt = "너는 블로그 글 제목을 만드는 어시스턴트야."
    user_prompt = f"'{keyword}'에 대한 블로그 글 제목 하나만 만들어줘. 다른 설명은 필요 없어. 예: 고구마의 효능과 요리법"
    return request_ai(api_key, user_prompt, system_prompt)

def generate_blog_idea(api_key: str):
    system_prompt = "너는 글 주제를 제안하는 블로그 어시스턴트야."
    user_prompt = "어제 한국 사람들이 주목한 식재료 한가지만 알려줘. 설명은 필요 없어 식재료만 간단하게 단답형으로 알려줘. 따옴표 사용하지마. 예: 고구마"
    return request_ai(api_key, user_prompt, system_prompt)

def generate_filename(title: str, api_key: str) -> str:
    user_prompt = f"'{title}' 앞의 제목을 참고해서 15자 이내의 영어로 마크다운 파일명 만들어줘. 다른 설명은 필요 없어. 확장자 빼고 파일명만 간단하게. 따옴표 사용하지말고. 특수문자 사용하지 말고. 예: sweet-potato-benefits"
    return request_ai(api_key, user_prompt)

def generate_post(prompt: str, api_key: str) -> str:
    system_prompt = "당신은 블로그 작가입니다. 마크다운 형식으로 작성해 주세요. 50대 이상의 한국인 독자를 대상으로 합니다. 글의 맨 앞과 뒤에 ```markdown 태그를 넣지 마세요."
    user_prompt = prompt
    return request_ai(api_key, user_prompt, system_prompt)

def save_post_to_file(title: str, filetitle: str, content: str, blog_path: str):
    date_str = datetime.now().strftime('%Y-%m-%d')
    filename = f"{date_str}-{filetitle.replace(' ', '-').lower()}.md"
    filepath = os.path.join(blog_path, '_posts', filename)

    post = frontmatter.Post(content, **{
        'title': title,
        'categories': 'Health',
        'toc': True,
        'toc_label': f"{title}",
        'toc_icon': 'tags',
        'toc_sticky': True,
        # 'categories': ['자동생성'],
        # 'tags': ['openrouter', 'python', '자동화']
    })

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(frontmatter.dumps(post))

    print(f"[+] {filename} 저장 완료")
    return filepath

def commit_and_push(blog_path: str, commit_msg: str):
    subprocess.run(['git', 'add', '.'], cwd=blog_path)
    subprocess.run(['git', 'commit', '-m', commit_msg], cwd=blog_path)
    subprocess.run(['git', 'push'], cwd=blog_path)
    print("[+] GitHub 블로그에 푸시 완료")

def auto_post(api_key, blog_path):
    keyword = generate_blog_idea(api_key)
    time.sleep(3)  # 3초 대기 (API 호출 제한 방지)
    title = generate_title(keyword, api_key)
    time.sleep(3)  # 3초 대기 (API 호출 제한 방지)
    content = generate_post(f"제목은 '{title}'이고, 블로그 글을 작성해줘. 글 맨 앞과 뒤에 ```markdown 이 태그 넣지말고.", api_key)
    time.sleep(3)  # 3초 대기 (API 호출 제한 방지)
    filetitle = generate_filename(title, api_key)
    filepath = save_post_to_file(title, filetitle, content, blog_path)
    commit_and_push(blog_path, f"Auto post: {title}")

if __name__ == "__main__":
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY") # OpenRouter API 키 입력
    BLOG_PATH = os.getcwd()  # GitHub 블로그 경로

    auto_post(OPENROUTER_API_KEY, BLOG_PATH)
