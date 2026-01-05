/**
 * AI Presentation Generator - Progressive Enhancement
 * Lightweight JavaScript for form handling and UI states
 */

(function() {
  'use strict';
  
  // Get DOM elements
  const form = document.querySelector('.generator-form');
  const textarea = document.getElementById('content');
  const submitButton = document.querySelector('.btn-primary');
  const statusMessage = document.getElementById('status-message');
  
  if (!form || !textarea || !submitButton) {
    return; // Exit if elements not found
  }
  
  /**
   * Update button state
   */
  function setButtonLoading(isLoading) {
    if (isLoading) {
      submitButton.classList.add('is-loading');
      submitButton.disabled = true;
      submitButton.querySelector('.btn-text').textContent = 'Generating…';
    } else {
      submitButton.classList.remove('is-loading');
      submitButton.disabled = false;
      submitButton.querySelector('.btn-text').textContent = 'Generate PPTX';
    }
  }
  
  /**
   * Update status message for screen readers
   */
  function updateStatus(message) {
    if (statusMessage) {
      statusMessage.textContent = message;
    }
  }
  
  /**
   * Validate textarea content
   */
  function validateContent() {
    const content = textarea.value.trim();
    const minLength = parseInt(textarea.getAttribute('minlength') || '100', 10);
    const maxLength = parseInt(textarea.getAttribute('maxlength') || '5000', 10);
    
    if (content.length < minLength) {
      return {
        valid: false,
        message: `Please enter at least ${minLength} characters. Current: ${content.length}`
      };
    }
    
    if (content.length > maxLength) {
      return {
        valid: false,
        message: `Content is too long. Maximum ${maxLength} characters. Current: ${content.length}`
      };
    }
    
    return { valid: true };
  }
  
  /**
   * Show temporary toast notification
   */
  function showToast(message, type = 'success') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    toast.textContent = message;
    
    // Add styles
    Object.assign(toast.style, {
      position: 'fixed',
      bottom: '24px',
      right: '24px',
      padding: '16px 24px',
      background: type === 'success' ? 'var(--success)' : 'var(--accent)',
      color: 'white',
      borderRadius: 'var(--radius-sm)',
      boxShadow: 'var(--shadow-3)',
      fontWeight: '500',
      fontSize: '0.9375rem',
      zIndex: '1000',
      opacity: '0',
      transform: 'translateY(10px)',
      transition: 'opacity 0.3s ease, transform 0.3s ease',
      maxWidth: '320px'
    });
    
    document.body.appendChild(toast);
    
    // Animate in
    requestAnimationFrame(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateY(0)';
    });
    
    // Remove after delay
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => {
        document.body.removeChild(toast);
      }, 300);
    }, 4000);
  }
  
  /**
   * Handle form submission
   */
  function handleSubmit(event) {
    event.preventDefault();
    
    // Validate content
    const validation = validateContent();
    if (!validation.valid) {
      updateStatus(validation.message);
      showToast(validation.message, 'error');
      textarea.focus();
      return;
    }
    
    // Set loading state
    setButtonLoading(true);
    updateStatus('Generating presentation, please wait...');
    
    // Simulate API call (replace with actual API call in production)
    setTimeout(() => {
      // Success state
      setButtonLoading(false);
      updateStatus('Presentation generated successfully!');
      showToast('✓ Presentation generated successfully!', 'success');
      
      // Optional: Clear form or download file
      // textarea.value = '';
      
    }, 2500);
  }
  
  /**
   * Character counter (optional enhancement)
   */
  function updateCharacterCount() {
    const length = textarea.value.length;
    const minLength = parseInt(textarea.getAttribute('minlength') || '100', 10);
    const maxLength = parseInt(textarea.getAttribute('maxlength') || '5000', 10);
    
    // You could add a character counter element here
    // For now, we'll just validate on submit
  }
  
  /**
   * Initialize
   */
  function init() {
    // Add form submit listener
    form.addEventListener('submit', handleSubmit);
    
    // Optional: Add input listener for real-time validation
    textarea.addEventListener('input', updateCharacterCount);
    
    // Optional: Save draft to localStorage
    const savedDraft = localStorage.getItem('ai-pptx-draft');
    if (savedDraft && !textarea.value) {
      textarea.value = savedDraft;
    }
    
    // Auto-save draft
    let saveTimeout;
    textarea.addEventListener('input', () => {
      clearTimeout(saveTimeout);
      saveTimeout = setTimeout(() => {
        localStorage.setItem('ai-pptx-draft', textarea.value);
      }, 1000);
    });
    
    // Clear draft on successful submit
    form.addEventListener('submit', () => {
      setTimeout(() => {
        localStorage.removeItem('ai-pptx-draft');
      }, 3000);
    });
  }
  
  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  
})();
