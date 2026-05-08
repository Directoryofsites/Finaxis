const fs = require('fs');
const content = fs.readFileSync('c:/ContaPY2/frontend/lib/menuData.js', 'utf8');
const regex = /permission:\s*'([^']+)'/g;
let match;
const permissions = new Set();
while ((match = regex.exec(content)) !== null) {
    permissions.add(match[1]);
}
console.log(Array.from(permissions).join('\n'));
