() => {
    const social = {};

    // Ищем ссылки на социальные сети
    const socialPatterns = {
        facebook: /facebook\.com\/[a-zA-Z0-9.]+/i,
        instagram: /instagram\.com\/[a-zA-Z0-9_.]+/i,
        twitter: /twitter\.com\/[a-zA-Z0-9_]+/i,
        linkedin: /linkedin\.com\/(?:company|in)\/[a-zA-Z0-9_-]+/i
    };

    const links = document.querySelectorAll('a[href]');
    for (const link of links) {
        const href = link.href;
        for (const [platform, pattern] of Object.entries(socialPatterns)) {
            if (pattern.test(href) && !social[platform]) {
                social[platform] = href;
            }
        }
    }

    return Object.keys(social).length > 0 ? social : null;
}
