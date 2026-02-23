// 照片墙前端 - OSS 版本

const imageContainer = document.getElementById('gallery');
let images = []; // 所有图片数据
let displayedCount = 0; // 已显示的图片数量
let loading = false;

const batchSize = 10; // 每批加载的数量
const initialBatchCount = 5; // 初始加载批次
const scrolldistance = 1000; // 滚动加载距离

let currentImageIndex = 0;
let leftArrow;
let rightArrow;

// 配置文件路径（在生产环境中可以使用绝对路径）
const CONFIG_PATH = './config.public.json';

// ================== 初始化 ==================

let CONFIG = null;

// 加载配置文件
async function loadConfig() {
    try {
        const response = await fetch(CONFIG_PATH);
        CONFIG = await response.json();
        console.log('配置加载成功');
        return true;
    } catch (error) {
        console.error('配置加载失败:', error);
        alert('配置文件加载失败，请确保 config.public.json 存在！');
        return false;
    }
}

// 计算相恋天数
function calculateLoveDays() {
    const startDate = new Date('2020-01-01'); // 从 index.html 中读取
    const today = new Date();
    startDate.setHours(0, 0, 0, 0);
    today.setHours(0, 0, 0, 0);
    const timeDiff = today - startDate;
    const days = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
    document.getElementById('loveDays').innerText = days;
}

// ================== 加载图片 ==================

async function fetchAllImages() {
    try {
        if (!CONFIG) {
            console.error('配置未加载');
            return;
        }

        // 调用函数计算 API 获取图片列表
        const apiUrl = `${CONFIG.aliyun.fc.get_images_url}?limit=100&sort=date_desc`;
        const response = await fetch(apiUrl);
        const result = await response.json();

        if (result.success) {
            images = result.data;
            console.log(`成功加载 ${images.length} 张图片`);
        } else {
            throw new Error(result.error || '获取图片失败');
        }

    } catch (error) {
        console.error('获取图片列表失败:', error);
        imageContainer.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 60px 20px; color: #999;">
                <p>图片加载失败: ${error.message}</p>
                <p>请检查函数计算 API 是否正确配置</p>
            </div>
        `;
    }
}

// 加载一批图片
async function loadImages(batchCount = 1) {
    if (loading) return;
    loading = true;

    for (let b = 0; b < batchCount; b++) {
        for (let i = 0; i < batchSize; i++) {
            if (displayedCount >= images.length) {
                window.removeEventListener('scroll', handleScroll);
                console.log('所有图片已加载完成');
                loading = false;
                return;
            }

            const image = images[displayedCount];
            const imgElement = createImageElement(image, displayedCount);
            imageContainer.appendChild(imgElement);

            displayedCount++;
        }
    }

    loading = false;
}

// 创建图片元素
function createImageElement(imageData, index) {
    const imgElement = document.createElement('img');

    // 设置缩略图 URL
    imgElement.src = imageData.thumbnail_url;
    imgElement.alt = imageData.filename;
    imgElement.setAttribute('data-large', imageData.url);
    imgElement.setAttribute('data-index', index);

    // 设置元数据
    const { metadata } = imageData;
    const dateTime = metadata.date ?
        `${metadata.date} ${metadata.time || ''}`.trim() :
        '';
    imgElement.setAttribute('data-date', dateTime);

    // 点击事件
    imgElement.addEventListener('click', function () {
        showPopup(
            this.getAttribute('data-large'),
            this.getAttribute('data-date'),
            parseInt(this.getAttribute('data-index'))
        );
    });

    imgElement.style.cursor = 'pointer';
    imgElement.classList.add('thumbnail');
    imgElement.loading = 'lazy';

    return imgElement;
}

// ================== 弹窗功能 ==================

function showPopup(src, date, index) {
    currentImageIndex = index;
    const popup = document.getElementById('popup');
    const popupImg = document.getElementById('popupImg');
    const imgDate = document.getElementById('imgDate');

    popup.style.display = 'block';
    popupImg.style.display = 'none';
    imgDate.innerText = '';

    const fullImg = new Image();
    fullImg.crossOrigin = 'Anonymous';
    fullImg.src = src;

    fullImg.onload = function () {
        popupImg.src = src;
        popupImg.style.display = 'block';
        imgDate.innerText = date;
    };

    fullImg.onerror = function () {
        imgDate.innerText = '加载失败';
    };

    leftArrow.style.display = 'flex';
    rightArrow.style.display = 'flex';

    if (currentImageIndex > 0) {
        leftArrow.classList.remove('disabled');
    } else {
        leftArrow.classList.add('disabled');
    }

    if (currentImageIndex < images.length - 1) {
        rightArrow.classList.remove('disabled');
    } else {
        rightArrow.classList.add('disabled');
    }
}

function closePopup() {
    const popup = document.getElementById('popup');
    const popupImg = document.getElementById('popupImg');
    const imgDate = document.getElementById('imgDate');
    popup.style.display = 'none';
    popupImg.src = '';
    imgDate.innerText = '';

    leftArrow.style.display = 'none';
    rightArrow.style.display = 'none';
}

// ================== 滚动加载 ==================

function handleScroll() {
    const scrollTop = window.scrollY;
    const windowHeight = window.innerHeight;
    const documentHeight = document.documentElement.scrollHeight;

    if (scrollTop + windowHeight >= documentHeight - scrolldistance) {
        loadImages();
    }
}

// ================== 图片导航 ==================

function showPreviousImage() {
    const prevIndex = currentImageIndex - 1;
    if (prevIndex >= 0 && images[prevIndex]) {
        currentImageIndex = prevIndex;
        const imgData = images[prevIndex];
        const dateTime = imgData.metadata.date ?
            `${imgData.metadata.date} ${imgData.metadata.time || ''}`.trim() :
            '';
        showPopup(imgData.url, dateTime, prevIndex);
    } else {
        leftArrow.classList.add('disabled');
    }
}

function showNextImage() {
    const nextIndex = currentImageIndex + 1;
    if (nextIndex < images.length && images[nextIndex]) {
        currentImageIndex = nextIndex;
        const imgData = images[nextIndex];
        const dateTime = imgData.metadata.date ?
            `${imgData.metadata.date} ${imgData.metadata.time || ''}`.trim() :
            '';
        showPopup(imgData.url, dateTime, nextIndex);
    } else {
        rightArrow.classList.add('disabled');
    }
}

// ================== 键盘事件 ==================

window.addEventListener('keydown', function (event) {
    const popup = document.getElementById('popup');
    if (popup.style.display === 'block') {
        if (event.key === 'ArrowLeft') {
            showPreviousImage();
        } else if (event.key === 'ArrowRight') {
            showNextImage();
        } else if (event.key === 'Escape') {
            closePopup();
        }
    }
});

// ================== 页面加载 ==================

window.onload = async function () {
    calculateLoveDays();

    // 加载配置
    const configLoaded = await loadConfig();
    if (!configLoaded) {
        return;
    }

    // 获取所有图片数据
    await fetchAllImages();

    // 加载初始批次
    await loadImages(initialBatchCount);

    // 设置滚动监听
    window.addEventListener('scroll', handleScroll);

    // 设置弹窗按钮
    document.getElementById('closeBtn').addEventListener('click', closePopup);

    leftArrow = document.getElementById('leftArrow');
    rightArrow = document.getElementById('rightArrow');

    leftArrow.addEventListener('click', showPreviousImage);
    rightArrow.addEventListener('click', showNextImage);

    leftArrow.style.display = 'none';
    rightArrow.style.display = 'none';
};
