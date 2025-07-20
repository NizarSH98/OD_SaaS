// Modern Dashboard Functionality
class ModernDashboard {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupSorting();
        this.setupAnimations();
        this.loadStats();
    }
    
    setupSorting() {
        const sortSelect = document.getElementById('sortProjects');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.sortProjects(e.target.value);
            });
        }
    }
    
    setupAnimations() {
        // Animate cards on load
        const cards = document.querySelectorAll('.stat-card, .project-card, .action-card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.transition = 'all 0.3s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 50);
        });
        
        // Hover effects for interactive elements
        this.setupHoverEffects();
    }
    
    setupHoverEffects() {
        // Project card hover effects
        const projectCards = document.querySelectorAll('.project-card');
        projectCards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-4px)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0)';
            });
        });
    }
    
    sortProjects(criteria) {
        const projectsGrid = document.querySelector('.projects-grid');
        if (!projectsGrid) return;
        
        const projects = Array.from(projectsGrid.children);
        
        projects.sort((a, b) => {
            switch (criteria) {
                case 'name':
                    const nameA = a.querySelector('.project-name').textContent.trim();
                    const nameB = b.querySelector('.project-name').textContent.trim();
                    return nameA.localeCompare(nameB);
                    
                case 'frames':
                    const framesA = parseInt(a.querySelector('.project-stat span').textContent) || 0;
                    const framesB = parseInt(b.querySelector('.project-stat span').textContent) || 0;
                    return framesB - framesA;
                    
                case 'recent':
                default:
                    // Keep original order for recent
                    return 0;
            }
        });
        
        // Animate reordering
        projects.forEach((project, index) => {
            project.style.transition = 'all 0.3s ease';
            project.style.transform = 'translateY(10px)';
            project.style.opacity = '0.7';
            
            setTimeout(() => {
                projectsGrid.appendChild(project);
                project.style.transform = 'translateY(0)';
                project.style.opacity = '1';
            }, index * 50);
        });
    }
    
    loadStats() {
        // This would load real statistics from the server
        // For now, we'll animate the existing values
        this.animateStatValues();
    }
    
    animateStatValues() {
        const statValues = document.querySelectorAll('.stat-value');
        statValues.forEach((element, index) => {
            const finalValue = element.textContent;
            const isNumeric = /^\d+/.test(finalValue);
            
            if (isNumeric) {
                const finalNumber = parseInt(finalValue.replace(/[^\d]/g, ''));
                this.animateNumber(element, 0, finalNumber, 1000, index * 200);
            }
        });
    }
    
    animateNumber(element, start, end, duration, delay) {
        setTimeout(() => {
            const startTime = performance.now();
            const originalText = element.textContent;
            
            const animate = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                
                // Easing function
                const easeOutCubic = 1 - Math.pow(1 - progress, 3);
                const current = Math.floor(start + (end - start) * easeOutCubic);
                
                // Preserve formatting
                if (originalText.includes(',')) {
                    element.textContent = current.toLocaleString();
                } else {
                    element.textContent = current.toString();
                }
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    element.textContent = originalText; // Restore original formatting
                }
            };
            
            requestAnimationFrame(animate);
        }, delay);
    }
    
    showNotification(message, type = 'info') {
        if (window.VisionLabel) {
            window.VisionLabel.showNotification(message, type);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new ModernDashboard();
}); 