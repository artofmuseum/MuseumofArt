// Modern Homepage JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Content Filter Tabs
    const filterTabs = document.querySelectorAll('.filter-tab');
    const contentSections = document.querySelectorAll('.content-section');
    
    filterTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const filterType = this.dataset.filter;
            
            // Remove active class from all tabs
            filterTabs.forEach(t => t.classList.remove('active'));
            
            // Add active class to clicked tab
            this.classList.add('active');
            
            // Filter content based on type
            filterContent(filterType);
        });
    });
    
    function filterContent(filterType) {
        // This function can be expanded to filter content dynamically
        console.log('Filtering content by:', filterType);
        
        // Example: Show/hide different content sections
        contentSections.forEach(section => {
            if (section.dataset.type === filterType) {
                section.style.display = 'block';
            } else {
                section.style.display = 'none';
            }
        });
    }
    
    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Intersection Observer for animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    const animateElements = document.querySelectorAll('.feature-card, .post-card, .stat-item');
    animateElements.forEach(el => {
        observer.observe(el);
    });
    
    // Newsletter form handling
    const newsletterForm = document.querySelector('.newsletter-form');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const emailInput = this.querySelector('input[type="email"]');
            const email = emailInput.value;
            
            if (email) {
                // Show loading state
                const submitBtn = this.querySelector('.btn-subscribe');
                const originalText = submitBtn.textContent;
                submitBtn.textContent = 'Gönderiliyor...';
                submitBtn.disabled = true;
                
                // Simulate form submission
                setTimeout(() => {
                    submitBtn.textContent = 'Başarılı!';
                    submitBtn.style.background = '#10b981';
                    
                    setTimeout(() => {
                        submitBtn.textContent = originalText;
                        submitBtn.disabled = false;
                        submitBtn.style.background = '';
                        emailInput.value = '';
                    }, 2000);
                }, 1000);
            }
        });
    }
    
    // Hero section parallax effect
    const heroSection = document.querySelector('.modern-hero');
    if (heroSection) {
        window.addEventListener('scroll', function() {
            const scrolled = window.pageYOffset;
            const rate = scrolled * -0.5;
            
            const heroPattern = heroSection.querySelector('.hero-pattern');
            if (heroPattern) {
                heroPattern.style.transform = `translateY(${rate}px)`;
            }
        });
    }
    
    // Card hover effects
    const cards = document.querySelectorAll('.feature-card, .post-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Stats counter animation
    const statNumbers = document.querySelectorAll('.stat-number');
    statNumbers.forEach(stat => {
        const target = parseInt(stat.textContent);
        const increment = target / 50;
        let current = 0;
        
        const updateCounter = () => {
            if (current < target) {
                current += increment;
                stat.textContent = Math.ceil(current);
                requestAnimationFrame(updateCounter);
            } else {
                stat.textContent = target;
            }
        };
        
        // Start animation when element is visible
        const statObserver = new IntersectionObserver(function(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    updateCounter();
                    statObserver.unobserve(entry.target);
                }
            });
        });
        
        statObserver.observe(stat);
    });
    
    // Search functionality
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            
            searchTimeout = setTimeout(() => {
                const query = this.value.trim();
                if (query.length > 2) {
                    performSearch(query);
                }
            }, 300);
        });
    }
    
    function performSearch(query) {
        // Implement search functionality here
        console.log('Searching for:', query);
        
        // Example: Make AJAX request to search endpoint
        fetch(`/search?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                // Handle search results
                console.log('Search results:', data);
            })
            .catch(error => {
                console.error('Search error:', error);
            });
    }
    
    // Mobile menu toggle
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const mobileMenu = document.querySelector('.mobile-menu');
    
    if (mobileMenuToggle && mobileMenu) {
        mobileMenuToggle.addEventListener('click', function() {
            this.classList.toggle('active');
            mobileMenu.classList.toggle('active');
        });
    }
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', function(e) {
        if (mobileMenu && mobileMenu.classList.contains('active')) {
            if (!mobileMenu.contains(e.target) && !mobileMenuToggle.contains(e.target)) {
                mobileMenu.classList.remove('active');
                mobileMenuToggle.classList.remove('active');
            }
        }
    });
    
    // Lazy loading for images
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => {
        imageObserver.observe(img);
    });
    
    // Smooth reveal animations
    const revealElements = document.querySelectorAll('.reveal');
    const revealObserver = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    revealElements.forEach(el => {
        revealObserver.observe(el);
    });
});

// Utility functions
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

// Export for use in other scripts
window.ModernHomepage = {
    debounce,
    throttle
}; 