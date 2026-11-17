/* Static syntax only. Never load, transpile or evaluate module configuration. */
'use strict';
const fs = require('node:fs');
const ts = require('typescript');

if (ts.version !== '6.0.3') throw new Error('unsupported TypeScript parser version');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const kind = /\.tsx$/.test(input.path) ? ts.ScriptKind.TSX : /\.jsx$/.test(input.path) ? ts.ScriptKind.JSX
  : /\.[cm]?ts$/.test(input.path) ? ts.ScriptKind.TS : ts.ScriptKind.JS;
const file = ts.createSourceFile(input.path, input.text, ts.ScriptTarget.Latest, true, kind);
const result = { imports: [], literals: [], commands: [], errors: [] };
const aliases = new Map();
const processModules = new Set(['child_process', 'node:child_process', 'worker_threads', 'node:worker_threads', 'module', 'node:module', 'vm', 'node:vm', 'process', 'node:process']);
const syntaxModules = new Set([...processModules, '@playwright/test']);
const line = node => file.getLineAndCharacterOfPosition(node.getStart(file)).line + 1;
const text = node => node && ts.isStringLiteralLike(node) ? node.text : null;
const error = (node, message) => result.errors.push([line(node), message]);
const reflectiveProcess = target => /^process\.(?:chdir|dlopen|getBuiltinModule|binding|_linkedBinding|execve|loadEnvFile|mainModule)(?:\.|$)/.test(target);
const name = node => {
  const value = !node ? '' : ts.isIdentifier(node) ? (aliases.get(node.text) || node.text)
    : ts.isCallExpression(node) && name(node.expression) === 'require' && node.arguments.length === 1
      && ['process', 'node:process'].includes(text(node.arguments[0])) ? 'process'
    : ts.isPropertyAccessExpression(node) ? name(node.expression) + '.' + node.name.text
    : ts.isElementAccessExpression(node) && text(node.argumentExpression) !== null
      ? name(node.expression) + '.' + text(node.argumentExpression) : '';
  return value.replace(/^(?:globalThis|global)\.(?=(?:process|require)(?:\.|$))/, '')
    .replace(/^process\.default(?=\.|$)/, 'process');
};
const literal = node => {
  if (ts.isStringLiteralLike(node)) return node.text;
  if (ts.isArrayLiteralExpression(node)) {
    const entries = node.elements.map(literal);
    return entries.every(entry => typeof entry === 'string') ? entries : undefined;
  }
  return undefined;
};
function bind(binding, prefix) {
  if (ts.isIdentifier(binding)) aliases.set(binding.text, prefix);
  else if (ts.isObjectBindingPattern(binding)) for (const item of binding.elements) {
    if (!ts.isIdentifier(item.name) || item.dotDotDotToken || (item.propertyName && !ts.isIdentifier(item.propertyName))) {
      error(item, 'unsupported reflective process/import binding');
    } else aliases.set(item.name.text, prefix + '.' + (item.propertyName || item.name).text);
  }
}
function imported(node, specifier) {
  const value = text(specifier);
  if (value === null) error(node, 'unresolved computed JavaScript import');
  else result.imports.push([line(node), value]);
}
function options(node) {
  if (!node) return {};
  if (!ts.isObjectLiteralExpression(node)) throw new Error('unresolved JavaScript process options');
  const result = {};
  for (const entry of node.properties) {
    if (!ts.isPropertyAssignment(entry) || ts.isComputedPropertyName(entry.name))
      throw new Error('unresolved JavaScript process option');
    const key = entry.name.text;
    if (key === 'cwd') {
      result.cwd = text(entry.initializer);
      if (result.cwd === null) throw new Error('unresolved JavaScript process cwd');
    } else if (['env', 'shell', 'execPath', 'execArgv'].includes(key)) {
      throw new Error('unsupported JavaScript process resolution option: ' + key);
    }
  }
  return result;
}
function staticConfig(node) {
  if (text(node) !== null || ts.isObjectLiteralExpression(node)) return true;
  if (ts.isAsExpression(node) || ts.isSatisfiesExpression(node) || ts.isParenthesizedExpression(node)) return staticConfig(node.expression);
  if (ts.isSpreadElement(node)) return staticConfig(node.expression);
  if (ts.isArrayLiteralExpression(node)) return node.elements.every(staticConfig);
  if (ts.isConditionalExpression(node)) return staticConfig(node.whenTrue) && staticConfig(node.whenFalse);
  return false;
}
function visit(node) {
  const scoped = ts.isBlock(node) || ts.isFunctionLike(node);
  const savedAliases = scoped ? new Map(aliases) : null;
  if (ts.isFunctionLike(node)) for (const parameter of node.parameters || []) {
    if (ts.isIdentifier(parameter.name)) {
      aliases.delete(parameter.name.text);
    }
  }
  if (ts.isImportDeclaration(node)) {
    imported(node, node.moduleSpecifier);
    if (syntaxModules.has(text(node.moduleSpecifier)) && node.importClause) {
      const moduleName = text(node.moduleSpecifier) === '@playwright/test' ? 'playwright' : text(node.moduleSpecifier).replace('node:', '');
      const clause = node.importClause;
      if (clause.name) bind(clause.name, moduleName);
      const bindings = clause.namedBindings;
      if (bindings && ts.isNamespaceImport(bindings)) bind(bindings.name, moduleName);
      else if (bindings) for (const entry of bindings.elements) {
        const importedName = (entry.propertyName || entry.name).text;
        aliases.set(entry.name.text, importedName === 'default' && processModules.has(text(node.moduleSpecifier))
          ? moduleName : moduleName + '.' + importedName);
      }
    }
  }
  if (ts.isExportDeclaration(node) && node.moduleSpecifier) {
    imported(node, node.moduleSpecifier);
    if (processModules.has(text(node.moduleSpecifier))) error(node, 'unsupported JavaScript process API re-export');
  }
  if (ts.isImportEqualsDeclaration(node) && ts.isExternalModuleReference(node.moduleReference)) {
    imported(node, node.moduleReference.expression);
    if (processModules.has(text(node.moduleReference.expression)))
      bind(node.name, text(node.moduleReference.expression).replace('node:', ''));
  }
  if (ts.isVariableDeclaration(node) && node.initializer) {
    const init = node.initializer;
    if (ts.isCallExpression(init) && name(init.expression) === 'require' && text(init.arguments[0]) !== null) {
      if (processModules.has(text(init.arguments[0]))) bind(node.name, text(init.arguments[0]).replace('node:', ''));
    } else {
      const target = name(init);
      if (/^(?:child_process|worker_threads|module|vm|process)(?:\.|$)/.test(target)
          || ['globalThis', 'global', 'require', 'eval', 'Function', 'globalThis.eval', 'global.eval', 'globalThis.Function', 'global.Function', 'process.chdir', 'process.dlopen', 'process.getBuiltinModule'].includes(target)) bind(node.name, target);
    }
  }
  if (ts.isStringLiteralLike(node)) result.literals.push([line(node), node.text]);
  if (ts.isPropertyAssignment(node) && ['globalSetup', 'globalTeardown', 'testDir', 'tsconfig'].includes(node.name.text)) {
    if (text(node.initializer) === null) error(node, 'unresolved computed JavaScript test configuration');
  }
  if (ts.isPropertyAssignment(node) && node.name.text === 'reporter' && !staticConfig(node.initializer))
    error(node, 'unresolved computed JavaScript reporter configuration');
  if (ts.isPropertyAssignment(node) && node.name.text === 'webServer') {
    const servers = ts.isArrayLiteralExpression(node.initializer) ? node.initializer.elements : [node.initializer];
    for (const server of servers) {
      if (!ts.isObjectLiteralExpression(server)) { error(node, 'unresolved JavaScript webServer configuration'); continue; }
      const entries = new Map(server.properties.filter(ts.isPropertyAssignment).map(property => [property.name.text, property.initializer]));
      const command = text(entries.get('command'));
      if (command === null) error(node, 'unresolved computed JavaScript webServer command');
      else if (entries.has('cwd') && text(entries.get('cwd')) === null) error(node, 'unresolved JavaScript webServer cwd');
      else result.commands.push({ line: line(node), command, ...(entries.has('cwd') ? {cwd: text(entries.get('cwd'))} : {}) });
    }
  }
  if (ts.isCallExpression(node) || ts.isNewExpression(node)) {
    const target = name(node.expression);
    const args = node.arguments || [];
    if (['defineConfig', 'playwright.defineConfig'].includes(target)) {
      if (args.length !== 1 || !ts.isObjectLiteralExpression(args[0])) error(node, 'unresolved JavaScript test configuration object');
    } else if (node.expression.kind === ts.SyntaxKind.ImportKeyword || ['require', 'require.resolve', 'module.require'].includes(target)) {
      if (args.length !== 1) error(node, 'unsupported JavaScript import arguments');
      else {
        imported(node, args[0]);
        if (node.expression.kind === ts.SyntaxKind.ImportKeyword && processModules.has(text(args[0])))
          error(node, 'unsupported dynamic JavaScript process-module import');
        if (target === 'require' && processModules.has(text(args[0]))
            && !(ts.isVariableDeclaration(node.parent) && node.parent.initializer === node)
            && !(['process', 'node:process'].includes(text(args[0]))
              && (ts.isPropertyAccessExpression(node.parent) || ts.isElementAccessExpression(node.parent))
              && ['process.env', 'process.argv', 'process.exit'].includes(name(node.parent))))
          error(node, 'unsupported inline JavaScript process-module require');
      }
    } else if (reflectiveProcess(target) || ['eval', 'Function', 'globalThis.eval', 'global.eval', 'globalThis.Function', 'global.Function', 'module.createRequire'].includes(target)) {
      error(node, 'unsupported reflective JavaScript execution: ' + target);
    } else if (target.startsWith('vm.')) {
      error(node, 'unresolved JavaScript VM/config execution');
    } else if (target.startsWith('worker_threads.') || target === 'Worker') {
      error(node, 'unsupported JavaScript worker execution');
    } else if (target.startsWith('child_process.')) {
      try {
        const api = target.slice('child_process.'.length);
        if (['exec', 'execSync'].includes(api)) {
          const command = text(args[0]);
          if (command === null) throw new Error('unresolved computed JavaScript process command');
          result.commands.push({line: line(node), command, ...options(args[1] && !ts.isFunctionLike(args[1]) ? args[1] : null)});
        } else if (['execFile', 'execFileSync', 'spawn', 'spawnSync'].includes(api)) {
          const command = text(args[0]);
          const operands = args[1] ? literal(args[1]) : [];
          if (command === null || !Array.isArray(operands)) throw new Error('unresolved computed JavaScript process arguments');
          result.commands.push({line: line(node), argv: [command, ...operands], ...options(args[2] && !ts.isFunctionLike(args[2]) ? args[2] : null)});
        } else throw new Error('unsupported JavaScript process API: ' + target);
      } catch (failure) { error(node, failure.message); }
    } else if (['Object.assign', 'Object.defineProperty', 'Reflect.set', 'Reflect.defineProperty'].includes(target) && name(args[0]) === 'process.env') {
      error(node, 'unsupported JavaScript environment mutation affecting resolution');
    } else if (ts.isElementAccessExpression(node.expression) && /^(?:child_process|module|worker_threads)$/.test(name(node.expression.expression))) {
      error(node, 'unresolved reflective JavaScript process/import API');
    }
  }
  if (ts.isElementAccessExpression(node)
      && (/^(?:child_process|module|worker_threads|vm|process)$/.test(name(node.expression)) || reflectiveProcess(name(node.expression)))
      && text(node.argumentExpression) === null) error(node, 'unresolved reflective JavaScript process/import API');
  if (ts.isIdentifier(node) || ts.isPropertyAccessExpression(node) || ts.isElementAccessExpression(node)) {
    const target = name(node);
    if (['process', 'globalThis', 'global'].includes(target) || reflectiveProcess(target) || /^(?:child_process|worker_threads|module|vm)(?:\.|$)/.test(target) || ['require', 'eval', 'Function', 'globalThis.eval', 'global.eval', 'globalThis.Function', 'global.Function', 'process.chdir', 'process.dlopen', 'process.getBuiltinModule'].includes(target)) {
      const parent = node.parent;
      const declaration = (ts.isVariableDeclaration(parent) && (parent.name === node || parent.initializer === node))
        || ts.isImportClause(parent) || ts.isImportSpecifier(parent) || ts.isNamespaceImport(parent) || ts.isImportEqualsDeclaration(parent)
        || ts.isBindingElement(parent) || ts.isPropertyAccessExpression(parent) || ts.isElementAccessExpression(parent)
        || ts.isPropertyAssignment(parent) && parent.name === node;
      const invocation = (ts.isCallExpression(parent) || ts.isNewExpression(parent)) && parent.expression === node;
      if (!declaration && !invocation) error(node, 'unsupported JavaScript process/import API escape');
    }
  }
  const mutation = ts.isDeleteExpression(node) ? node.expression
    : ts.isBinaryExpression(node) && node.operatorToken.kind >= ts.SyntaxKind.FirstAssignment
      && node.operatorToken.kind <= ts.SyntaxKind.LastAssignment ? node.left : null;
  if (mutation) {
    const target = name(mutation);
    if (target === 'process.env' || /^process\.env\.(?:PATH|NODE_PATH|NODE_OPTIONS)$/.test(target)
        || (/^process\.env$/.test(name(mutation.expression)) && !target))
      error(node, 'unsupported JavaScript environment change affecting resolution');
  }
  ts.forEachChild(node, visit);
  if (scoped) {
    aliases.clear(); for (const entry of savedAliases) aliases.set(...entry);
  }
}
for (const diagnostic of file.parseDiagnostics) error(file, ts.flattenDiagnosticMessageText(diagnostic.messageText, ' '));
visit(file);
process.stdout.write(JSON.stringify(result));
