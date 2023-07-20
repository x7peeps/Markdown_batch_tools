import misaka
import os
import requests
import uuid
import fnmatch
from bs4 import BeautifulSoup
import argparse



proxies = {
        "http": "http://127.0.0.1:1087",
        "https": "http://127.0.0.1:1087",
    }

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
    try:
        img_data = requests.get(url,timeout=3).content
        
    except Exception as e:
        print("❌，使用代理",end="")

        try:
            img_data = requests.get(url, proxies=proxies).content
            
        except Exception as e:
            print(f"Failed to download image from {url} to {file}: {e}")
        pass
    filename = os.path.basename(file).replace('.md','')
    dirname = os.path.dirname(file)
    targer_dir = os.path.join(dirname, f'{filename}.assets')
    
    
    # 若图片地址在文件夹中，则不再下载
    if "assets" in url:
        return False
    if not os.path.exists(targer_dir):
        os.mkdir(targer_dir)
    pic_filename = f'{uuid.uuid4().hex}.jpg'
    with open(os.path.join(targer_dir, pic_filename), 'w+') as f:
        f.buffer.write(img_data)
    
    return f"./{filename}.assets/{pic_filename}"


# 将文档名称放在文档的第一行
def update_md_filenames(folder_path):
    # # 从文件路径中提取文件名
    # filename = os.path.basename(filepath)

    # # 读取原始文件内容
    # with open(filepath, 'r', encoding='utf-8') as file:
    #     content = file.read()

    # # 将文件名添加到内容的前面
    # new_content = filename + "\n" + content

    # # 将新内容写回文件
    # with open(filepath, 'w', encoding='utf-8') as file:
    #     file.write(new_content)
    print('正在处理文件首行...')
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                file_name = os.path.splitext(file)[0]
                with open(file_path, "r+") as f:
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
            print(f'正在下载第 {index + 1} 张图片...',end="")
            try:
                if "http" not in pic:
                    print("⏩")
                    continue
                new_img_path=download_pics(pic, file)
                if new_img_path:
                    new_content = md_content.replace(pic, new_img_path)
                    with open(file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print("✅")
                else:# 若返回false则跳过
                    print("⏩")
                    continue
            except Exception as e:
                if new_img_path == False:
                    print("⏩")
                    print(f'图片{pic}已存在，跳过')
                else:    
                    print("❌")
                    print(f'下载{pic}失败：{e}')
                pass
            
        # soup = BeautifulSoup(md_content, 'lxml')
        # for img in soup.find_all('img'):
        #     url = img.get('src')
        #     content = content.replace(url, new_img_path)
        f.close()
        print(f'处理完成。')    
if __name__ == '__main__':
    # 创建 ArgumentParser 对象
    parser = argparse.ArgumentParser(description='This is a project to download pic from markdown.')

    # 添加参数
    parser.add_argument('-f', '--folder', help='folder path, default is ./files', default=os.path.abspath(os.path.join('.', 'files')))

    # 解析参数
    args = parser.parse_args()
    FolderPATH = args.folder
    main(FolderPATH)
        
    # 处理md文档内容首行，确保所有文件的首行为文件名
    # 判断文件首行是否为文件名
    # 判断首行是否为文件名
    # 获取文件名
    
    update_md_filenames(FolderPATH)
    
    