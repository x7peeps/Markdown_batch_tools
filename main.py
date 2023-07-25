import misaka
import os
import requests
import hashlib
import fnmatch
from bs4 import BeautifulSoup
import argparse
from urllib.parse import urlparse

def get_files_list(dir):
    """
    获取一个目录下所有文件列表，包括子目录
    :param dir:
    :return:
    """
    files_list = []
    for root, dirs, files in os.walk(dir, topdown=False):
        for file in files:
            if fnmatch.fnmatch(file, '*.md'):
                files_list.append(os.path.join(root, file))
    return files_list

def get_pics_list(md_content):
    """
    获取一个markdown文档里的所有图片链接
    :param md_content:
    :return:
    """
    md_render = misaka.Markdown(misaka.HtmlRenderer())
    html = md_render(md_content)
    soup = BeautifulSoup(html, features='html.parser')
    pics_list = []
    for img in soup.find_all('img'):
        pics_list.append(img.get('src'))
    return pics_list

def download_pics(url, file):
    """
    下载图片并保存到本地
    """
    # 生成图片的MD5哈希值作为文件名
    file_name = hashlib.md5(url.encode()).hexdigest() + '.jpg'
    # 拼接保存路径
    save_path = os.path.join(os.path.dirname(file), f"{os.path.splitext(os.path.basename(file))[0]}.assets", file_name)
    if DEBUG:
        print(f"save_path:{save_path}")
    # 判断文件是否已存在，若存在直接返回文件路径
    if os.path.exists(save_path):
        return save_path
    try:
        # 发起请求下载图片
        img_data = requests.get(url, timeout=3, verify=True).content
    except Exception as e:
        print("❌，ssl不使用认证尝试", end="")
        try:
            img_data = requests.get(url, timeout=3, verify=False).content
        except Exception as e:
            if DEBUG:
                print(f"Failed to download image from {url} to {file}: {e}")
            return None
    # 创建目录
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'wb') as f:
        f.write(img_data)
    # 获取相对路径
    relative_path = os.path.relpath(save_path, os.path.dirname(file))
    return relative_path

def is_valid_url(url):
    try:
        response = requests.head(url)
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.RequestException:
        return False

def update_md_filenames(folder_path):
    print('正在处理文件首行...')
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                file_name = os.path.splitext(file)[0]
                with open(file_path, "r+", encoding='utf-8') as f:
                    if not f.readline().endswith('file_name\n'):
                        content = f.read()
                        f.seek(0, 0)
                        f.write(f"{file_name}\n{content}")
                        f.close()
                    else:
                        print(f'文件{file}首行已经是文件名，跳过')
                        continue
    print('处理完成。')

def main(FolderPATH):
    # 使用参数
    print(f'The file path is {FolderPATH}')
    # 切换到文件所在的目录
    os.chdir(FolderPATH)
    print(f'切换到目录：{FolderPATH}')
    print(f'当前目录：{os.getcwd()}')
    files_list = get_files_list(FolderPATH)
    for file in files_list:
        # 判断文件名是否为md，若不是则绕过
        if not file.endswith('.md'):
            print(f'跳过：{file}')
            continue
        print(f'正在处理：{file}')
        with open(file, encoding='utf-8') as f:
            md_content = f.read()
        pics_list = get_pics_list(md_content)
        print(f'发现图片 {len(pics_list)} 张')
        for index, pic in enumerate(pics_list):
            if DEBUG:
                print(f'正在下载第 {index + 1} 张图片...{pic}', end="")
            else:
                print(f'正在下载第 {index + 1} 张图片...',end='')
            try:
                if "http" not in pic:
                    if DEBUG:
                        print("nohttp⏩")
                    else:
                        print("⏩")
                    continue
                # 判断如果包含xss相关的异常字符则不要进行下载
                try:
                    xss_words = [">", "<"]
                    for i in xss_words:
                        if i in pic:
                            if DEBUG:
                                print("xsswd⏩", end="")
                            else:
                                print("⏩")
                            continue
                except Exception as _:
                    if DEBUG:
                        print(f"error detail :{_}")
                    pass
                new_img_path = download_pics(pic, file)
                if new_img_path:
                    new_content = md_content.replace(pic, new_img_path)
                    md_content = new_content 
                    if DEBUG:
                        print(f"\nnew_img_path:{new_img_path}")
                    print(f"✅")
                else:
                    print("else⏩")
                    if DEBUG:
                        print(f"\nnew_img_path:{new_img_path}")
                    continue
            except Exception as e:
                if DEBUG:
                    print(f'下载{pic}失败：{e}')
                continue
        with open(file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f'处理完成。')

if __name__ == '__main__':
    # 创建 ArgumentParser 对象
    parser = argparse.ArgumentParser(description='This is a project to download pic from markdown.')
    # 添加参数
    parser.add_argument('-f', '--folder', help='folder path, default is ./files', default=os.path.abspath(os.path.join('.', 'files')))
    parser.add_argument('-p', '--proxy', help='proxy, default is 127.0.0.1:1087', default='127.0.0.1:1087')
    parser.add_argument('-d', '--debug', help='debug mode', action='store_true')
    # 解析参数
    args = parser.parse_args()
    FolderPATH = args.folder
    PROXY = args.proxy
    DEBUG = args.debug
    try:
        main(FolderPATH)
        # 处理md文档内容首行，确保所有文件的首行为文件名
        update_md_filenames(FolderPATH)
    except Exception as e:
        if DEBUG:
            print(f'处理失败：{e}')
        parser.print_help()
        exit(1)
