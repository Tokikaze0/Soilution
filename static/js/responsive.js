// ========================================
// RESPONSIVE JAVASCRIPT - SOILUTION WEBSITE
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    
    // ========================================
    // MOBILE NAVIGATION HANDLING
    // ========================================
    
    // Handle mobile menu toggle
    const mobileMenuToggle = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (mobileMenuToggle && navbarCollapse) {
        mobileMenuToggle.addEventListener('click', function() {
            navbarCollapse.classList.toggle('show');
        });
        
        // Close mobile menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!mobileMenuToggle.contains(event.target) && !navbarCollapse.contains(event.target)) {
                navbarCollapse.classList.remove('show');
            }
        });
    }
    
    // ========================================
    // SIDEBAR HANDLING FOR MOBILE
    // ========================================
    
    // Handle sidebar toggle on mobile
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    const sidebarOverlay = document.querySelector('.sidebar-overlay');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
            if (sidebarOverlay) {
                sidebarOverlay.classList.toggle('active');
            }
        });
        
        // Close sidebar when clicking overlay
        if (sidebarOverlay) {
            sidebarOverlay.addEventListener('click', function() {
                sidebar.classList.remove('open');
                sidebarOverlay.classList.remove('active');
            });
        }
    }
    
    // ========================================
    // INBOX SIDEBAR HANDLING
    // ========================================
    
    // Handle inbox sidebar toggle
    const inboxToggle = document.getElementById('inbox-toggle');
    const inboxSidebar = document.getElementById('inbox-sidebar');
    
    if (inboxToggle && inboxSidebar) {
        inboxToggle.addEventListener('click', function(e) {
            e.preventDefault();
            inboxSidebar.classList.toggle('hidden');
            inboxSidebar.classList.toggle('translate-x-full');
        });
        
        // Close inbox sidebar when clicking outside
        document.addEventListener('click', function(event) {
            if (!inboxToggle.contains(event.target) && !inboxSidebar.contains(event.target)) {
                inboxSidebar.classList.add('hidden');
                inboxSidebar.classList.add('translate-x-full');
            }
        });
    }
    
    // ========================================
    // RESPONSIVE TABLE HANDLING
    // ========================================
    
    // Add data labels to table cells for mobile stacking
    function addTableDataLabels() {
        const tables = document.querySelectorAll('.table-stack-mobile');
        
        tables.forEach(table => {
            const headers = table.querySelectorAll('th');
            const rows = table.querySelectorAll('tbody tr');
            
            headers.forEach((header, index) => {
                const label = header.textContent.trim();
                rows.forEach(row => {
                    const cell = row.querySelectorAll('td')[index];
                    if (cell) {
                        cell.setAttribute('data-label', label);
                    }
                });
            });
        });
    }
    
    // Call function on page load
    addTableDataLabels();
    
    // ========================================
    // TOUCH-FRIENDLY INTERACTIONS
    // ========================================
    
    // Add touch feedback to buttons
    const touchButtons = document.querySelectorAll('.btn, .nav-link, .dropdown-item');
    
    touchButtons.forEach(button => {
        button.addEventListener('touchstart', function() {
            this.style.transform = 'scale(0.95)';
        });
        
        button.addEventListener('touchend', function() {
            this.style.transform = 'scale(1)';
        });
    });
    
    // ========================================
    // RESPONSIVE CHART HANDLING
    // ========================================
    
    // Handle chart resizing
    function resizeCharts() {
        const charts = document.querySelectorAll('.chart-container');
        
        charts.forEach(chart => {
            if (chart.chart) {
                chart.chart.resize();
            }
        });
    }
    
    // Resize charts on window resize
    window.addEventListener('resize', resizeCharts);
    
    // ========================================
    // MOBILE-SPECIFIC FEATURES
    // ========================================
    
    // Detect mobile device
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (isMobile) {
        // Add mobile-specific classes
        document.body.classList.add('mobile-device');
        
        // Prevent zoom on input focus (iOS)
        const inputs = document.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('focus', function() {
                this.style.fontSize = '16px';
            });
        });
        
        // Handle mobile scroll behavior
        let touchStartY = 0;
        let touchEndY = 0;
        
        document.addEventListener('touchstart', function(e) {
            touchStartY = e.touches[0].clientY;
        });
        
        document.addEventListener('touchend', function(e) {
            touchEndY = e.changedTouches[0].clientY;
            handleSwipe();
        });
        
        function handleSwipe() {
            const swipeThreshold = 50;
            const diff = touchStartY - touchEndY;
            
            if (Math.abs(diff) > swipeThreshold) {
                if (diff > 0) {
                    // Swipe up
                    console.log('Swipe up detected');
                } else {
                    // Swipe down
                    console.log('Swipe down detected');
                }
            }
        }
    }
    
    // ========================================
    // PERFORMANCE OPTIMIZATIONS
    // ========================================
    
    // Lazy load images
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
    
    // ========================================
    // UTILITY FUNCTIONS
    // ========================================
    
    // Debounce function for performance
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Throttle function for scroll events
    function throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
    
    // ========================================
    // RESPONSIVE UTILITIES
    // ========================================
    
    // Add responsive classes based on screen size
    function updateResponsiveClasses() {
        const width = window.innerWidth;
        const body = document.body;
        
        // Remove existing responsive classes
        body.classList.remove('mobile', 'tablet', 'desktop');
        
        // Add appropriate class
        if (width < 768) {
            body.classList.add('mobile');
        } else if (width < 992) {
            body.classList.add('tablet');
        } else {
            body.classList.add('desktop');
        }
    }
    
    // Update classes on load and resize
    updateResponsiveClasses();
    window.addEventListener('resize', debounce(updateResponsiveClasses, 250));
    
    // ========================================
    // ACCESSIBILITY IMPROVEMENTS
    // ========================================
    
    // Add keyboard navigation support
    document.addEventListener('keydown', function(e) {
        // Escape key closes modals and sidebars
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            const sidebars = document.querySelectorAll('.sidebar.open');
            
            modals.forEach(modal => {
                const closeBtn = modal.querySelector('.btn-close');
                if (closeBtn) closeBtn.click();
            });
            
            sidebars.forEach(sidebar => {
                sidebar.classList.remove('open');
            });
        }
    });
    
    // ========================================
    // ERROR HANDLING
    // ========================================
    
    // Handle JavaScript errors gracefully
    window.addEventListener('error', function(e) {
        console.error('JavaScript error:', e.error);
        // You can add error reporting here
    });
    
    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', function(e) {
        console.error('Unhandled promise rejection:', e.reason);
        // You can add error reporting here
    });
    
});

// ========================================
// EXPORT FUNCTIONS FOR GLOBAL USE
// ========================================

// Make functions available globally if needed
window.ResponsiveUtils = {
    addTableDataLabels: function() {
        // Re-export the function for global use
        const tables = document.querySelectorAll('.table-stack-mobile');
        tables.forEach(table => {
            const headers = table.querySelectorAll('th');
            const rows = table.querySelectorAll('tbody tr');
            
            headers.forEach((header, index) => {
                const label = header.textContent.trim();
                rows.forEach(row => {
                    const cell = row.querySelectorAll('td')[index];
                    if (cell) {
                        cell.setAttribute('data-label', label);
                    }
                });
            });
        });
    },
    
    resizeCharts: function() {
        const charts = document.querySelectorAll('.chart-container');
        charts.forEach(chart => {
            if (chart.chart) {
                chart.chart.resize();
            }
        });
    }
};
