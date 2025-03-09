export default defineContentScript({
  matches: ['*://*.tiktok.com/*'],
  main() {
    let credibilityScore = 0;

    function createCredibilityElement() {
      const credibilityElement = document.createElement('button');
      credibilityElement.type = 'button';
      credibilityElement.className = 'css-1ncfmqs-ButtonActionItem e1hk3hf90';
      credibilityElement.style.display = 'flex';
      credibilityElement.style.alignItems = 'center';
      
      const iconSpan = document.createElement('span');
      iconSpan.className = 'css-whg6mn-SpanIconWrapper e1hk3hf91';
      iconSpan.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="rgba(255, 255, 255, .9)">
          <path d="M10 1.66667C5.4 1.66667 1.66667 5.4 1.66667 10C1.66667 14.6 5.4 18.3333 10 18.3333C14.6 18.3333 18.3333 14.6 18.3333 10C18.3333 5.4 14.6 1.66667 10 1.66667ZM10.8333 14.1667H9.16667V12.5H10.8333V14.1667ZM10.8333 10.8333H9.16667V5.83333H10.8333V10.8333Z"/>
        </svg>
      `;

      const scoreText = document.createElement('strong');
      scoreText.className = 'css-1w013xe-StrongText e1hk3hf92';
      scoreText.textContent = `${credibilityScore}%`;
      scoreText.dataset.credibilityScore = 'true';

      credibilityElement.appendChild(iconSpan);
      credibilityElement.appendChild(scoreText);

      return credibilityElement;
    }

    function updateCredibilityDisplay() {
      const existingScore = document.querySelector('[data-credibility-score]');
      if (existingScore) {
        existingScore.textContent = `${credibilityScore}%`;
      }
    }

    function injectCredibilityScore() {
      const actionsContainer = document.querySelector('.css-1d39a26-DivFlexCenterRow.ehlq8k31');
      if (actionsContainer && !document.querySelector('[data-credibility-score]')) {
        const credibilityElement = createCredibilityElement();
        actionsContainer.insertBefore(credibilityElement, actionsContainer.children[1]);
      }
    }

    // Listen for credibility score updates from the popup
    chrome.runtime.onMessage.addListener((message) => {
      if (message.type === 'credibilityUpdate') {
        credibilityScore = message.credibility;
        updateCredibilityDisplay();
      }
    });

    // Watch for video changes (TikTok is a SPA)
    const observer = new MutationObserver(() => {
      if (window.location.href !== lastUrl) {
        lastUrl = window.location.href;
        setTimeout(injectCredibilityScore, 1000); // Give time for the new video UI to load
      }
    });

    let lastUrl = window.location.href;
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    // Initial injection
    setTimeout(injectCredibilityScore, 1000);
  },
});
