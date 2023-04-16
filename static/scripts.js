// Variables
var terminal = document.getElementById('terminal');
var frostedRectangle = document.querySelector('.frosted-rectangle');
var terminal = document.getElementById('terminal');

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Toggle terminal visibility on button click
    setupTerminalToggle();

    // Toggle senders-text visibility on arrow click
    setupSendersTextToggle();

    // Toggle settings-text visibility on arrow click
    setupSettingsTextToggle();
  
    // Add and remove account input fields
    setupAccountFields();
});

// Add event listener to the API key input
var apiKeyInput = document.getElementById('api-key-input');
apiKeyInput.addEventListener('input', function () {
    if (this.value) {
        this.classList.add('no-underline');
    } else {
        this.classList.remove('no-underline');
    }
});

// Functions
function setupTerminalToggle() {
    const terminalToggleButton = document.getElementById('terminal-toggle-button');
    const settingsButton = document.getElementById('settings-button');
    const centeredContainer = document.querySelector('.centered-container');
    const settingsContainer = document.querySelector('.settings-container');
    const terminal = document.getElementById('terminal');

    terminalToggleButton.addEventListener('click', () => {
        terminal.classList.toggle('blurred');
        centeredContainer.classList.toggle('hidden');
        settingsButton.classList.toggle('hidden');
        if (!settingsContainer.classList.contains('hidden')) {
            settingsContainer.classList.add('hidden');
        }
    });

    settingsButton.addEventListener('click', () => {
        centeredContainer.classList.toggle('hidden');
        settingsContainer.classList.toggle('hidden');
        terminalToggleButton.classList.toggle('hidden');
    });
}

function setupSendersTextToggle() {
    var arrow = document.getElementById('arrow');
    var sendersText = document.getElementById('senders-text');

    arrow.addEventListener('click', function() {
        sendersText.classList.toggle('expanded');
        arrow.style.transform = sendersText.classList.contains('expanded') ? 'rotate(180deg)' : 'rotate(0deg)';
    });
}

function setupSettingsTextToggle() {
    const openaiHeader = document.getElementById('openai-arrow');
    const openaiText = document.getElementById('openai-text');
    const accountsHeader = document.getElementById('accounts-arrow');
    const accountsText = document.getElementById('accounts-text');
    const apiKeyInput = document.getElementById('api-key-input');
    const checkMark = document.createElement('span');
    checkMark.innerHTML = '&#x2714;'; // Check mark character
    checkMark.classList.add('check-mark');

    apiKeyInput.parentNode.insertBefore(checkMark, apiKeyInput.nextSibling);

    openaiHeader.addEventListener('click', () => {
        openaiText.classList.toggle('expanded');
        openaiHeader.style.transform = openaiText.classList.contains('expanded') ? 'rotate(180deg)' : '';
    });

    accountsHeader.addEventListener('click', () => {
        accountsText.classList.toggle('expanded');
        accountsHeader.style.transform = accountsText.classList.contains('expanded') ? 'rotate(180deg)' : '';
    });

    apiKeyInput.addEventListener('input', () => {
        if (apiKeyInput.value) {
            checkMark.style.display = 'inline';
            apiKeyInput.classList.add('filled');
        } else {
            checkMark.style.display = 'none';
            apiKeyInput.classList.remove('filled');
        }
    });

    apiKeyInput.addEventListener('blur', () => {
        checkMark.style.display = 'none';
    });

    checkMark.addEventListener('click', () => {
        // Confirm the changes here (e.g., save the API key)
        checkMark.style.display = 'none';
    });
}

function setupAccountFields() {
    const addAccountBtn = document.querySelector('.add-account');
    const removeAccountBtn = document.querySelector('.remove-account');
    const accountList = document.querySelector('.account-list');
    const emailProviders = {
        "gmail": "imap.gmail.com",
        "outlook": "imap-mail.outlook.com",
        "yahoo": "imap.mail.yahoo.com",
        "aol": "imap.aol.com",
        "icloud": "imap.mail.me.com",
        "zoho": "imap.zoho.com",
        "gmx": "imap.gmx.com",
        "fastmail": "imap.fastmail.com",
        "protonmail": "imap.protonmail.com", // ProtonMail requires a paid plan and Bridge for IMAP access
        "office365": "outlook.office365.com",
        "mailru": "imap.mail.ru",
        "yandex": "imap.yandex.com",
        "cpanel": "mail.yourdomain.com", // Replace 'yourdomain.com' with your actual domain
        "dovecot": "mail.yourdomain.com", // Replace 'yourdomain.com' with your actual domain
        "courier": "mail.yourdomain.com", // Replace 'yourdomain.com' with your actual domain
        "hmailserver": "mail.yourdomain.com", // Replace 'yourdomain.com' with your actual domain
    };

    addAccountBtn.addEventListener('click', () => {
        const accountDiv = document.createElement('div');
        accountDiv.classList.add('account');

        const emailInput = document.createElement('input');
        emailInput.type = 'email';
        emailInput.placeholder = 'Email';
        emailInput.classList.add('account-input');

        const passwordInput = document.createElement('input');
        passwordInput.type = 'password';
        passwordInput.placeholder = 'Password';
        passwordInput.classList.add('account-input');

        const providerSelect = document.createElement('select');
        providerSelect.classList.add('provider-select');

        for (const provider in emailProviders) {
            const option = document.createElement('option');
            option.value = emailProviders[provider];
            option.textContent = provider;
            providerSelect.appendChild(option);
        }

        accountDiv.appendChild(emailInput);
        accountDiv.appendChild(passwordInput);
        accountDiv.appendChild(providerSelect);
        accountList.appendChild(accountDiv);
    });

    removeAccountBtn.addEventListener('click', () => {
        if (accountList.childElementCount > 0) {
            accountList.removeChild(accountList.lastChild);
        }
    });
}

function updateLogs() {
    // ... existing code ...
}

// Simulate receiving the summary after 3 seconds
setTimeout(function() {
    // Add the summary text below the existing text in the frosted rectangle
    var summary = document.createElement('p');
    summary.textContent = 'This is a paragraph summary returned by OpenAI.';
    frostedRectangle.appendChild(summary);

    // Animate the frosted rectangle by increasing its max-height
    frostedRectangle.style.maxHeight = '800px';
    frostedRectangle.style.paddingBottom = '40px';
}, 3000);
