import streamlit as st
import pandas as pd
import urllib.parse
import requests
from bs4 import BeautifulSoup
import re

# Hàm tạo URL dựa trên từ khóa
def generate_url_with_keyword(keyword, page_number):
    base_url = "https://timkiem.vnexpress.net/"
    
    query_params = {
        'q': keyword,
        'media_type': 'text',
        'fromdate': '',
        'todate': '',
        'latest': 'on',
        'cate_code': '',
        'search_f': 'title,tag_list',
        'date_format': 'week',
        'page': page_number
    }
    
    query_string = urllib.parse.urlencode(query_params, doseq=True)
    full_url = f"{base_url}?{query_string}"
    
    return full_url

# Hàm lấy nội dung bài báo
def layscript(url):
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    paragraphs = soup.find_all('p', class_='Normal')
    article_text = '. '.join([paragraph.get_text() for paragraph in paragraphs])
    
    sentences = re.split(r'(?<!\d)\.\s+', article_text.strip())
    if len(sentences) > 1:
        article_text = ' '.join(sentences[:-1])
        
    return article_text

# Hàm lấy ngày đăng bài báo
def laydate(url):
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    date = soup.find('span', class_='date')
    return date.get_text() if date else "Không rõ"

# Hàm chính để cào bài báo theo từ khóa và số lượng bài báo
def layscriptbao_theokeyword(keywords, sobaibao, progress_bar, status_text):
    page_number = 1
    data = []
    seen_titles = set()
    count = 0
    total_articles = sobaibao

    while count < sobaibao:
        url = generate_url_with_keyword(keywords, page_number)
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        container = soup.find('div', class_='width_common list-news-subfolder')

        if container is None:
            break

        articles = container.find_all('a', href=True, title=True)
        new_articles_found = False

        for article in articles:
            if count >= sobaibao:
                break

            title = article.get('title')
            href = article.get('href')

            if title and href and title not in seen_titles:
                seen_titles.add(title)
                # Cập nhật progress bar
                count += 1
                data.append([title, href])
                
                # Cập nhật thanh tiến độ và hiển thị trạng thái
                progress_percentage = count / total_articles
                progress_bar.progress(progress_percentage)
                status_text.text(f"Đang cào bài báo {count}/{total_articles}")

                new_articles_found = True

        if not new_articles_found:
            break
        
        page_number += 1

    df = pd.DataFrame(data, columns=["Tiêu đề", "URL"])
    df['Nội dung'] = df['URL'].apply(layscript)
    df['Ngày đăng'] = df['URL'].apply(laydate)
    return df

# Giao diện Streamlit
def main():
    st.title('Ứng dụng cào dữ liệu từ VNExpress')

    # Nhập từ khóa và số lượng bài báo
    keyword = st.text_input('Nhập từ khóa tìm kiếm:')
    sobaibao = st.number_input('Số lượng bài báo cần cào:', min_value=1, max_value=100, value=1)

    if st.button('Cào dữ liệu'):
        if keyword:
            with st.spinner('Đang cào dữ liệu...'):
                # Tạo thanh tiến độ và hiển thị trạng thái
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Cào dữ liệu với thanh tiến độ
                df = layscriptbao_theokeyword(keyword, sobaibao, progress_bar, status_text)
            
            st.success("Cào dữ liệu hoàn tất!")
            
            # Hiển thị DataFrame
            st.dataframe(df)

            # Tạo file Excel tạm thời và cung cấp link tải về
            excel_filename = f"{keyword}_articles.xlsx"
            df.to_excel(excel_filename, index=False)
            
            with open(excel_filename, "rb") as file:
                st.download_button(
                    label="Tải về file Excel",
                    data=file,
                    file_name=excel_filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.error('Vui lòng nhập từ khóa!')

if __name__ == "__main__":
    main()
