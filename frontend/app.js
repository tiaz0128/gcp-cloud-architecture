// Configuration
const CONFIG = {
    DIAGRAM_TYPE: 'architecture-beta',
    LOCAL_API_URL: 'http://localhost:8080',
    PROD_API_URL: 'https://cloud-diagram-generator-hfqglxuxxa-du.a.run.app'
};

// Global state
let currentMermaidCode = '';
let mermaidCounter = 0;

// Initialize Mermaid
function initializeMermaid() {
    mermaid.initialize({
        startOnLoad: false,
        theme: 'default',
        securityLevel: 'loose',
        flowchart: { useMaxWidth: true, htmlLabels: true },
        architecture: { useMaxWidth: true, htmlLabels: true },
        dompurifyConfig: {
            USE_PROFILES: { svg: true, svgFilters: true },
            ADD_TAGS: ['iconify-icon'],
            ADD_ATTR: ['icon', 'width', 'height', 'inline']
        }
    });

    // Register icon packs
    mermaid.registerIconPacks([
        { name: 'gcp', loader: () => fetch(getIconUrl('gcp.json')).then(res => res.json()) },
        { name: 'azr', loader: () => fetch(getIconUrl('azr.json')).then(res => res.json()) },
        { name: 'aws', loader: () => fetch(getIconUrl('aws.json')).then(res => res.json()) }
    ]);
}

// Utility functions
function getIconUrl(filename) {
    const baseUrl = window.location.origin + window.location.pathname.replace(/\/[^\/]*$/, '');
    
    if (window.location.hostname.includes('storage.googleapis.com')) {
        const pathParts = window.location.pathname.split('/');
        const bucketName = pathParts[1] || window.location.hostname.split('.')[0];
        return `https://storage.googleapis.com/${bucketName}/icons/${filename}`;
    }
    
    return `${baseUrl}/icons/${filename}`;
}

function getApiBaseUrl() {
    const metaApiUrl = document.querySelector('meta[name="api-base-url"]');
    if (metaApiUrl && metaApiUrl.content) {
        return metaApiUrl.content;
    }

    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return CONFIG.LOCAL_API_URL;
    }

    if (window.location.hostname.includes('storage.googleapis.com')) {
        console.warn('Cloud Storage 호스팅에서 API URL이 메타 태그로 설정되지 않았습니다.');
        return CONFIG.PROD_API_URL;
    }

    return CONFIG.PROD_API_URL;
}

// DOM manipulation
function showLoading() {
    const container = document.getElementById('diagramContainer');
    const placeholder = document.getElementById('placeholder');
    const actions = document.getElementById('diagramActions');
    const loading = document.getElementById('loading');
    
    // Hide existing diagrams first
    if (container) {
        const existingDiagrams = container.querySelectorAll('div:not(#placeholder):not(#loading)');
        existingDiagrams.forEach(diagram => diagram.style.display = 'none');
    }
    
    // Hide other elements
    if (placeholder) placeholder.style.display = 'none';
    if (actions) actions.style.display = 'none';
    if (loading) loading.classList.add('show');

    // Update button
    const btnText = document.getElementById('btnText');
    const button = document.querySelector('.generate-btn');
    if (btnText) btnText.textContent = '생성 중...';
    if (button) button.disabled = true;
}

function hideLoading() {
    const loading = document.getElementById('loading');
    if (loading) loading.classList.remove('show');

    // Reset button
    const btnText = document.getElementById('btnText');
    const button = document.querySelector('.generate-btn');
    if (btnText) btnText.textContent = '다이어그램 생성';
    if (button) button.disabled = false;
}

function showDiagramActions() {
    const actionsElement = document.getElementById('diagramActions');
    if (actionsElement) {
        actionsElement.style.display = 'flex';
    }
}

function showError(message) {
    hideLoading();
    
    const container = document.getElementById('diagramContainer');
    const placeholder = document.getElementById('placeholder');

    if (container) {
        const existingDiagrams = container.querySelectorAll('div:not(#placeholder):not(#loading)');
        existingDiagrams.forEach(diagram => diagram.remove());

        if (placeholder) {
            placeholder.innerHTML = `
                <div class="placeholder-icon">⚠️</div>
                <h3>오류가 발생했습니다</h3>
                <div style="text-align: left; max-width: 400px; margin: 0 auto;">${message}</div>
            `;
            placeholder.style.display = 'block';
        }
    }
}

// Main functionality
async function generateDiagram() {
    const formData = new FormData(document.getElementById('diagramForm'));
    const requestData = {
        description: formData.get('description'),
        cloud_provider: formData.get('cloud_provider'),
        diagram_type: CONFIG.DIAGRAM_TYPE
    };

    showLoading();

    try {
        const API_BASE_URL = getApiBaseUrl();
        const response = await fetch(`${API_BASE_URL}/generate-diagram`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (!data.mermaid_code) {
            throw new Error('API 응답에 mermaid_code가 없습니다.');
        }

        currentMermaidCode = data.mermaid_code;
        await renderMermaidDiagram(currentMermaidCode);
        showDiagramActions();

    } catch (error) {
        console.error('API 에러:', error);
        
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            showError(`API 서버에 연결할 수 없습니다.<br><br>
                <strong>현재 API URL:</strong> ${getApiBaseUrl()}<br><br>
                <em>배포가 완료되었는지 확인하거나 잠시 후 다시 시도해주세요.</em>`);
        } else {
            showError(`다이어그램 생성에 실패했습니다.<br><br>
                <strong>오류:</strong> ${error.message}`);
        }
    }
}

async function renderMermaidDiagram(code) {
    const container = document.getElementById('diagramContainer');
    
    if (!container) {
        console.error('다이어그램 컨테이너를 찾을 수 없습니다');
        hideLoading();
        return;
    }

    try {
        // Clear existing diagrams
        const existingDiagrams = container.querySelectorAll('div:not(#placeholder):not(#loading)');
        existingDiagrams.forEach(diagram => diagram.remove());

        // Render with mermaid
        mermaidCounter++;
        const graphDefinition = `mermaid-${mermaidCounter}`;
        const renderResult = await mermaid.render(graphDefinition, code);

        // Insert SVG
        const svgContainer = document.createElement('div');
        svgContainer.style.textAlign = 'center';
        svgContainer.style.padding = '20px';
        svgContainer.innerHTML = renderResult.svg;

        container.appendChild(svgContainer);
        hideLoading();

    } catch (error) {
        console.error('Mermaid 렌더링 실패:', error);
        
        // Fallback method
        try {
            mermaidCounter++;
            const fallbackId = `mermaid-fallback-${mermaidCounter}`;

            const mermaidDiv = document.createElement('div');
            mermaidDiv.id = fallbackId;
            mermaidDiv.className = 'mermaid';
            mermaidDiv.style.textAlign = 'center';
            mermaidDiv.style.padding = '20px';
            mermaidDiv.textContent = code;

            container.appendChild(mermaidDiv);

            await new Promise(resolve => setTimeout(resolve, 200));

            const mermaidElement = document.getElementById(fallbackId);
            if (!mermaidElement) {
                throw new Error('Mermaid 요소를 찾을 수 없습니다.');
            }

            mermaidElement.removeAttribute('data-processed');
            mermaid.init(undefined, mermaidElement);
            hideLoading();

        } catch (fallbackError) {
            console.error('모든 렌더링 방법 실패:', fallbackError);
            showError(`다이어그램 렌더링에 실패했습니다.<br><br>
                <strong>Mermaid 코드:</strong><br>
                <pre style="background: #f5f5f5; padding: 15px; border-radius: 4px; font-size: 12px; overflow-x: auto; margin: 10px 0;">${code}</pre>
                <br><small>💡 이 코드를 <a href="https://mermaid.live" target="_blank">mermaid.live</a>에서 직접 테스트해보세요.</small>`);
        }
    }
}

// Download and export functions
function downloadDiagram(format) {
    const svg = document.querySelector('#diagramContainer svg');
    if (!svg) return;

    if (format === 'svg') {
        const svgData = new XMLSerializer().serializeToString(svg);
        const svgBlob = new Blob([svgData], { type: 'image/svg+xml' });
        const svgUrl = URL.createObjectURL(svgBlob);
        const link = document.createElement('a');
        link.href = svgUrl;
        link.download = 'cloud-architecture.svg';
        link.click();
        URL.revokeObjectURL(svgUrl);
    } else if (format === 'png') {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();

        const svgData = new XMLSerializer().serializeToString(svg);
        const svgBlob = new Blob([svgData], { type: 'image/svg+xml' });
        const svgUrl = URL.createObjectURL(svgBlob);

        img.onload = function () {
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);

            canvas.toBlob(function (blob) {
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = 'cloud-architecture.png';
                link.click();
                URL.revokeObjectURL(link.href);
            });

            URL.revokeObjectURL(svgUrl);
        };

        img.src = svgUrl;
    }
}

function copyMermaidCode() {
    if (currentMermaidCode) {
        navigator.clipboard.writeText(currentMermaidCode).then(() => {
            alert('Mermaid 코드가 클립보드에 복사되었습니다!');
        });
    }
}

// Event handlers
function setExample(text) {
    document.getElementById('description').value = text;
}

function handleExampleClick(event) {
    const example = event.target.closest('.example-item');
    if (example && example.dataset.example) {
        setExample(example.dataset.example);
    }
}

function handleActionClick(event) {
    const button = event.target.closest('.action-btn');
    if (!button) return;

    const action = button.dataset.action;
    switch (action) {
        case 'download-svg':
            downloadDiagram('svg');
            break;
        case 'download-png':
            downloadDiagram('png');
            break;
        case 'copy-code':
            copyMermaidCode();
            break;
    }
}

// Initialize app
function initializeApp() {
    initializeMermaid();

    // Form submission
    document.getElementById('diagramForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await generateDiagram();
    });

    // Example items - use event delegation
    document.querySelector('.examples').addEventListener('click', handleExampleClick);

    // Action buttons - use event delegation
    document.addEventListener('click', handleActionClick);

    console.log('앱 초기화 완료');
    console.log('API URL:', getApiBaseUrl());
}

// Start app when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeApp);