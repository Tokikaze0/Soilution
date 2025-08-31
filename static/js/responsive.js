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
        
        // Special handling for Chart.js charts
        const chartJsCharts = document.querySelectorAll('canvas[id*="Chart"]');
        chartJsCharts.forEach(canvas => {
            if (canvas.chart) {
                canvas.chart.resize();
            }
        });
    }
    
    // Resize charts on window resize
    window.addEventListener('resize', resizeCharts);
    
    // ========================================
    // MOBILE-SPECIFIC FEATURES
    // ========================================
    
    // Detect mobile device and screen size
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const isVerySmallScreen = window.innerWidth <= 320;
    const isSmallScreen = window.innerWidth <= 576;
    
    if (isMobile) {
        // Add mobile-specific classes
        document.body.classList.add('mobile-device');
        
        if (isVerySmallScreen) {
            document.body.classList.add('very-small-screen');
        }
        
        if (isSmallScreen) {
            document.body.classList.add('small-screen');
        }
        
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
        
        // Optimize for very small screens (320px)
        if (isVerySmallScreen) {
            optimizeForVerySmallScreen();
        }
    }
    
    // ========================================
    // VERY SMALL SCREEN OPTIMIZATIONS (320px)
    // ========================================
    
    function optimizeForVerySmallScreen() {
        // Reduce font sizes for better fit
        const textElements = document.querySelectorAll('h1, h2, h3, p, span, div');
        textElements.forEach(element => {
            if (element.style.fontSize) {
                const currentSize = parseFloat(element.style.fontSize);
                if (currentSize > 12) {
                    element.style.fontSize = (currentSize * 0.8) + 'px';
                }
            }
        });
        
        // Optimize chart display
        const charts = document.querySelectorAll('canvas[id*="Chart"]');
        charts.forEach(canvas => {
            if (canvas.chart && canvas.chart.options) {
                // Reduce chart padding and margins
                canvas.chart.options.layout.padding = {
                    top: 10,
                    right: 10,
                    bottom: 10,
                    left: 10
                };
                
                // Adjust legend position for small screens
                if (canvas.chart.options.plugins && canvas.chart.options.plugins.legend) {
                    canvas.chart.options.plugins.legend.position = 'bottom';
                    canvas.chart.options.plugins.legend.labels.fontSize = 10;
                }
                
                canvas.chart.update();
            }
        });
        
        // Optimize sidebar behavior
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            // Make sidebar more compact
            sidebar.style.width = '3.5rem';
            sidebar.addEventListener('mouseenter', function() {
                this.style.width = '8rem';
            });
            sidebar.addEventListener('mouseleave', function() {
                this.style.width = '3.5rem';
            });
        }
        
        // Optimize inbox sidebar
        const inboxSidebar = document.getElementById('inbox-sidebar');
        if (inboxSidebar) {
            inboxSidebar.style.width = '100%';
            inboxSidebar.style.right = '0';
        }
        
        // Optimize dropdowns
        const dropdowns = document.querySelectorAll('#profile-dropdown, #notification-dropdown');
        dropdowns.forEach(dropdown => {
            dropdown.style.right = '0';
            if (dropdown.id === 'profile-dropdown') {
                dropdown.style.width = '12rem';
            } else if (dropdown.id === 'notification-dropdown') {
                dropdown.style.width = '15rem';
            }
        });
        
        // Optimize main content padding
        const mainContent = document.querySelector('.flex-1.p-6.mt-16.ml-14');
        if (mainContent) {
            mainContent.style.padding = '0.75rem';
            mainContent.style.marginLeft = '3.5rem';
        }
        
        // Optimize stats grid
        const statsGrid = document.querySelector('.grid.grid-cols-2.md\\:grid-cols-4.lg\\:grid-cols-7');
        if (statsGrid) {
            statsGrid.style.gap = '0.5rem';
        }
        
        // Optimize stats cards
        const statsCards = document.querySelectorAll('.bg-white.p-4.rounded.shadow.border');
        statsCards.forEach(card => {
            card.style.padding = '0.75rem';
            card.style.marginBottom = '0.5rem';
            
            const title = card.querySelector('.text-lg');
            const value = card.querySelector('.text-2xl');
            const icon = card.querySelector('img');
            
            if (title) title.style.fontSize = '0.9rem';
            if (value) value.style.fontSize = '1.5rem';
            if (icon) {
                icon.style.width = '2.5rem';
                icon.style.height = '2.5rem';
            }
        });
        
        // Optimize chart container
        const chartContainer = document.querySelector('.card.mt-12.bg-white.border.border-gray-300.rounded-lg.shadow-lg.p-4');
        if (chartContainer) {
            chartContainer.style.marginTop = '1rem';
            chartContainer.style.padding = '0.75rem';
            
            const chartTitle = chartContainer.querySelector('h3');
            if (chartTitle) chartTitle.style.fontSize = '1rem';
        }
        
        // Optimize chart canvas
        const chartCanvas = document.getElementById('cropHistoryChart');
        if (chartCanvas) {
            chartCanvas.style.width = '100%';
            chartCanvas.style.height = '250px';
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
            setTimeout(later, wait);
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
        body.classList.remove('mobile', 'tablet', 'desktop', 'very-small-screen', 'small-screen');
        
        // Add appropriate class
        if (width <= 320) {
            body.classList.add('mobile', 'very-small-screen');
        } else if (width <= 576) {
            body.classList.add('mobile', 'small-screen');
        } else if (width < 768) {
            body.classList.add('mobile');
        } else if (width < 992) {
            body.classList.add('tablet');
        } else {
            body.classList.add('desktop');
        }
        
        // Re-optimize if screen size changes to very small
        if (width <= 320 && !body.classList.contains('very-small-optimized')) {
            body.classList.add('very-small-optimized');
            optimizeForVerySmallScreen();
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
    },
    
    optimizeForVerySmallScreen: function() {
        // Make this function available globally
        if (typeof optimizeForVerySmallScreen === 'function') {
            optimizeForVerySmallScreen();
        }
    }
};
