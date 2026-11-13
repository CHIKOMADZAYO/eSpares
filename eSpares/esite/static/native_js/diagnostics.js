(() => {
    const scanButton = document.getElementById('start-device-scan');
    const status = document.getElementById('device-scan-status');
    const results = document.getElementById('device-scan-results');
    const details = document.getElementById('device-scan-details');
    const deviceReference = document.getElementById('device-reference');

    if (!scanButton || !status || !results || !details || !deviceReference) return;

    const updateScanButton = () => {
        scanButton.disabled = deviceReference.value.trim().length === 0;
    };
    deviceReference.addEventListener('input', updateScanButton);
    updateScanButton();

    const getDeviceType = () => {
        if (navigator.userAgentData && typeof navigator.userAgentData.mobile === 'boolean') {
            return navigator.userAgentData.mobile ? 'Phone or tablet' : 'Computer';
        }
        return /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent)
            ? 'Phone or tablet (estimated)'
            : 'Computer (estimated)';
    };

    const getPlatform = () => {
        const reportedPlatform = navigator.userAgentData?.platform || navigator.platform || '';
        if (/Windows/i.test(reportedPlatform)) return 'Windows';
        if (/Mac/i.test(reportedPlatform)) return 'macOS';
        if (/Android/i.test(reportedPlatform)) return 'Android';
        if (/iPhone|iPad|iPod/i.test(navigator.userAgent)) return 'iOS or iPadOS';
        if (/Linux/i.test(reportedPlatform)) return 'Linux';
        if (/Chrome OS/i.test(navigator.userAgent)) return 'ChromeOS';
        return reportedPlatform || 'Not reported by this browser';
    };

    const getBrowser = () => {
        const brands = navigator.userAgentData?.brands;
        if (brands && brands.length) {
            const brand = brands.find((item) => !/not.?a.?brand/i.test(item.brand)) || brands[0];
            return `${brand.brand} ${brand.version}`;
        }

        const agent = navigator.userAgent;
        const browserPatterns = [
            [/Edg(?:e|A|iOS)?\/([\d.]+)/, 'Microsoft Edge'],
            [/Firefox\/([\d.]+)/, 'Firefox'],
            [/Chrome\/([\d.]+)/, 'Chrome'],
            [/Version\/([\d.]+).*Safari/, 'Safari'],
        ];
        for (const [pattern, name] of browserPatterns) {
            const match = agent.match(pattern);
            if (match) return `${name} ${match[1]}`;
        }
        return 'Browser could not be identified';
    };

    const addResult = (label, value) => {
        const term = document.createElement('dt');
        const description = document.createElement('dd');
        term.textContent = label;
        description.textContent = value;
        details.append(term, description);
    };

    scanButton.addEventListener('click', () => {
        const reference = deviceReference.value.trim();
        if (!reference) {
            status.textContent = 'Enter a model number or serial number to continue.';
            deviceReference.focus();
            return;
        }

        scanButton.disabled = true;
        status.textContent = 'Checking browser-reported device details…';

        try {
            const screenSize = window.screen
                ? `${window.screen.width} × ${window.screen.height} pixels`
                : 'Not available';
            const viewportSize = `${window.innerWidth} × ${window.innerHeight} pixels`;
            const connection = navigator.onLine
                ? 'Browser reports online; this does not guarantee internet access.'
                : 'Browser reports offline.';

            details.replaceChildren();
            addResult('Device reference entered', reference);
            addResult('Device category', getDeviceType());
            addResult('Platform', getPlatform());
            addResult('Browser', getBrowser());
            addResult('Connection', connection);
            addResult('Screen resolution', screenSize);
            addResult('Page viewport', viewportSize);
            addResult('Secure page context', window.isSecureContext ? 'Yes' : 'No');

            results.hidden = false;
            status.textContent = 'Scan complete. Results were displayed locally in this page.';
            results.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } catch (error) {
            status.textContent = 'The browser could not complete this check. You can still use manual troubleshooting below.';
        } finally {
            updateScanButton();
        }
    });
})();
