() => {
    // Пытаемся получить мета-описание
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc && metaDesc.content) {
        return metaDesc.content.trim();
    }

    // Пытаемся получить Open Graph описание
    const ogDesc = document.querySelector('meta[property="og:description"]');
    if (ogDesc && ogDesc.content) {
        return ogDesc.content.trim();
    }

    // Извлекаем текст из основного контента
    const mainContent = document.querySelector('main') ||
                       document.querySelector('article') ||
                       document.querySelector('.content') ||
                       document.querySelector('body');

    if (mainContent) {
        // Берем первые несколько параграфов
        const paragraphs = mainContent.querySelectorAll('p');
        const texts = Array.from(paragraphs)
            .slice(0, 3)
            .map(p => p.textContent.trim())
            .filter(text => text.length > 20);

        if (texts.length > 0) {
            return texts.join(' ').substring(0, 1000);
        }
    }

    return null;
}
