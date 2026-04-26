// Funcionalidad de navegación para manuales de Gestión de Recaudos

document.addEventListener('DOMContentLoaded', function() {
    // Navegación suave para enlaces internos
    const internalLinks = document.querySelectorAll('a[href^="#"]');
    internalLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Generar tabla de contenidos automáticamente
    generateTableOfContents();

    // Resaltar sección actual en navegación
    highlightCurrentSection();

    // Agregar funcionalidad de búsqueda si existe
    initializeSearch();
});

function generateTableOfContents() {
    const tocContainer = document.querySelector('.toc ul');
    if (!tocContainer) return;

    const headings = document.querySelectorAll('h2, h3');
    let tocHTML = '';

    headings.forEach((heading, index) => {
        // Crear ID si no existe
        if (!heading.id) {
            heading.id = `section-${index}`;
        }

        const level = heading.tagName === 'H2' ? 'toc-level-1' : 'toc-level-2';
        const indent = heading.tagName === 'H3' ? 'style="margin-left: 1rem;"' : '';
        
        tocHTML += `<li ${indent}><a href="#${heading.id}" class="${level}">${heading.textContent}</a></li>`;
    });

    tocContainer.innerHTML = tocHTML;
}

function highlightCurrentSection() {
    const sections = document.querySelectorAll('h2, h3');
    const tocLinks = document.querySelectorAll('.toc a');

    function updateActiveSection() {
        let currentSection = null;
        
        sections.forEach(section => {
            const rect = section.getBoundingClientRect();
            if (rect.top <= 100) {
                currentSection = section;
            }
        });

        // Remover clase activa de todos los enlaces
        tocLinks.forEach(link => link.classList.remove('active'));

        // Agregar clase activa al enlace correspondiente
        if (currentSection) {
            const activeLink = document.querySelector(`.toc a[href="#${currentSection.id}"]`);
            if (activeLink) {
                activeLink.classList.add('active');
            }
        }
    }

    // Agregar estilos para enlace activo
    const style = document.createElement('style');
    style.textContent = `
        .toc a.active {
            background: #4f46e5;
            color: white;
            font-weight: 600;
        }
    `;
    document.head.appendChild(style);

    window.addEventListener('scroll', updateActiveSection);
    updateActiveSection(); // Ejecutar al cargar
}

function initializeSearch() {
    const searchInput = document.querySelector('#manual-search');
    if (!searchInput) return;

    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const sections = document.querySelectorAll('.section');

        sections.forEach(section => {
            const text = section.textContent.toLowerCase();
            const isVisible = text.includes(searchTerm) || searchTerm === '';
            
            section.style.display = isVisible ? 'block' : 'none';
        });
    });
}

// Función para abrir manual desde botones externos
function openManual(manualPath) {
    window.open(manualPath, '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes');
}

// Función para imprimir manual
function printManual() {
    window.print();
}

// Función para exportar a PDF (requiere biblioteca externa)
function exportToPDF() {
    if (typeof html2pdf !== 'undefined') {
        const element = document.querySelector('.container');
        const opt = {
            margin: 1,
            filename: document.title + '.pdf',
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
        };
        html2pdf().set(opt).from(element).save();
    } else {
        alert('Funcionalidad de PDF no disponible. Use la opción de imprimir del navegador.');
    }
}

// Función para copiar enlace de sección
function copyLinkToSection(sectionId) {
    const url = window.location.href.split('#')[0] + '#' + sectionId;
    
    if (navigator.clipboard) {
        navigator.clipboard.writeText(url).then(() => {
            showNotification('Enlace copiado al portapapeles');
        });
    } else {
        // Fallback para navegadores más antiguos
        const textArea = document.createElement('textarea');
        textArea.value = url;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showNotification('Enlace copiado al portapapeles');
    }
}

function showNotification(message) {
    const notification = document.createElement('div');
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #22c55e;
        color: white;
        padding: 1rem;
        border-radius: 8px;
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Agregar estilos para animación de notificación
const notificationStyle = document.createElement('style');
notificationStyle.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(notificationStyle);