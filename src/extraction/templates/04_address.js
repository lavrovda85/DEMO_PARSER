() => {
    // Ищем адрес в различных местах
    const selectors = [
        '[itemprop="address"]',
        '.address', '.location', '.contact-address',
        '.store-address', '.business-address'
    ];

    for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element) {
            return element.textContent.trim();
        }
    }

    // Ищем в JSON-LD структурированных данных
    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
    for (const script of scripts) {
        try {
            const data = JSON.parse(script.textContent);
            if (data.address && typeof data.address === 'object') {
                const addr = data.address;
                return [addr.streetAddress, addr.addressLocality,
                       addr.addressRegion, addr.postalCode]
                       .filter(Boolean).join(', ');
            }
        } catch (e) {
            continue;
        }
    }

    return null;
}
