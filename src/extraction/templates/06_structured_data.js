() => {
    // Вспомогательная функция для извлечения микроданных
    function extractMicrodata(element) {
        const data = {};
        const itemType = element.getAttribute('itemtype');
        if (itemType) {
            data.type = itemType;
        }

        const properties = element.querySelectorAll('[itemprop]');
        for (const prop of properties) {
            const propName = prop.getAttribute('itemprop');
            let propValue;

            if (prop.hasAttribute('content')) {
                propValue = prop.getAttribute('content');
            } else if (prop.tagName === 'META') {
                propValue = prop.getAttribute('content');
            } else if (prop.tagName === 'AUDIO' || prop.tagName === 'VIDEO' || prop.tagName === 'SOURCE') {
                propValue = prop.getAttribute('src');
            } else if (prop.tagName === 'IMG') {
                propValue = prop.getAttribute('src');
            } else if (prop.tagName === 'TIME') {
                propValue = prop.getAttribute('datetime');
            } else {
                propValue = prop.textContent.trim();
            }

            if (propValue) {
                data[propName] = propValue;
            }
        }

        return data;
    }

    // Вспомогательная функция для извлечения данных из таблиц
    function extractTableData(table) {
        const rows = table.querySelectorAll('tr');
        if (rows.length === 0) return null;

        const tableData = {
            headers: [],
            rows: []
        };

        // Извлекаем заголовки
        const headerRow = table.querySelector('thead tr') || rows[0];
        if (headerRow) {
            const headers = headerRow.querySelectorAll('th, td');
            for (const header of headers) {
                tableData.headers.push(header.textContent.trim());
            }
        }

        // Извлекаем строки данных
        const dataRows = table.querySelectorAll('tbody tr') || rows;
        for (let i = 0; i < dataRows.length; i++) {
            // Пропускаем заголовок, если он был в первой строке
            if (headerRow === rows[0] && i === 0) continue;

            const cells = dataRows[i].querySelectorAll('td, th');
            const rowData = [];
            for (const cell of cells) {
                rowData.push(cell.textContent.trim());
            }
            if (rowData.length > 0) {
                tableData.rows.push(rowData);
            }
        }

        return tableData;
    }

    // Вспомогательная функция для извлечения свойств schema.org
    function extractSchemaProperties(element) {
        const properties = {};

        const propElements = element.querySelectorAll('[itemprop]');
        for (const prop of propElements) {
            const propName = prop.getAttribute('itemprop');
            let propValue;

            if (prop.hasAttribute('content')) {
                propValue = prop.getAttribute('content');
            } else if (prop.tagName === 'META') {
                propValue = prop.getAttribute('content');
            } else if (prop.tagName === 'A' && prop.hasAttribute('href')) {
                propValue = prop.getAttribute('href');
            } else if (prop.tagName === 'IMG' && prop.hasAttribute('src')) {
                propValue = prop.getAttribute('src');
            } else {
                propValue = prop.textContent.trim();
            }

            if (propValue) {
                properties[propName] = propValue;
            }
        }

        return properties;
    }

    const structuredData = {};

    // 1. Ищем JSON-LD структурированные данные
    const jsonLdScripts = document.querySelectorAll('script[type="application/ld+json"]');
    if (jsonLdScripts.length > 0) {
        structuredData.jsonLd = [];
        for (const script of jsonLdScripts) {
            try {
                const data = JSON.parse(script.textContent);
                structuredData.jsonLd.push(data);
            } catch (e) {
                // Игнорируем некорректный JSON
                continue;
            }
        }
    }

    // 2. Ищем микроданные (microdata)
    const microdataElements = document.querySelectorAll('[itemscope]');
    if (microdataElements.length > 0) {
        structuredData.microdata = [];
        for (const element of microdataElements) {
            const itemData = extractMicrodata(element);
            if (itemData && Object.keys(itemData).length > 0) {
                structuredData.microdata.push(itemData);
            }
        }
    }

    // 3. Ищем OpenGraph мета-теги
    const ogTags = {};
    const ogMetaTags = document.querySelectorAll('meta[property^="og:"]');
    for (const tag of ogMetaTags) {
        const property = tag.getAttribute('property').replace('og:', '');
        const content = tag.getAttribute('content');
        if (content) {
            ogTags[property] = content;
        }
    }
    if (Object.keys(ogTags).length > 0) {
        structuredData.openGraph = ogTags;
    }

    // 4. Ищем Twitter Card мета-теги
    const twitterTags = {};
    const twitterMetaTags = document.querySelectorAll('meta[name^="twitter:"]');
    for (const tag of twitterMetaTags) {
        const name = tag.getAttribute('name').replace('twitter:', '');
        const content = tag.getAttribute('content');
        if (content) {
            twitterTags[name] = content;
        }
    }
    if (Object.keys(twitterTags).length > 0) {
        structuredData.twitterCard = twitterTags;
    }

    // 5. Ищем таблицы с данными
    const dataTables = document.querySelectorAll('table');
    if (dataTables.length > 0) {
        structuredData.tables = [];
        for (const table of dataTables) {
            const tableData = extractTableData(table);
            if (tableData && tableData.rows && tableData.rows.length > 0) {
                structuredData.tables.push(tableData);
            }
        }
    }

    // 6. Ищем schema.org микроразметку
    const schemaElements = document.querySelectorAll('[itemtype]');
    if (schemaElements.length > 0) {
        structuredData.schemaOrg = [];
        for (const element of schemaElements) {
            const schemaData = {
                type: element.getAttribute('itemtype'),
                properties: extractSchemaProperties(element)
            };
            if (schemaData.properties && Object.keys(schemaData.properties).length > 0) {
                structuredData.schemaOrg.push(schemaData);
            }
        }
    }

    return Object.keys(structuredData).length > 0 ? structuredData : null;
}
