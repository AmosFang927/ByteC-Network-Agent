#!/usr/bin/env node

const { spawn } = require('child_process');

console.log('🔍 Debugging Context7 MCP Connection...');

// Test different connection scenarios
const tests = [
  {
    name: 'Test 1: Basic Connection',
    args: ['@upstash/context7-mcp', '--key', '2b9e200f-fe9c-4d20-85c2-1cd3ab2d1963']
  },
  {
    name: 'Test 2: With Profile', 
    args: ['@upstash/context7-mcp', '--key', '2b9e200f-fe9c-4d20-85c2-1cd3ab2d1963', '--profile', 'alleged-galliform-09YBkw']
  }
];

let currentTestIndex = 0;

function runTest(testConfig) {
  console.log(`\n🧪 ${testConfig.name}`);
  console.log('Args:', testConfig.args);
  
  const child = spawn('npx', ['-y', '@smithery/cli@latest', 'run', ...testConfig.args], {
    stdio: ['pipe', 'pipe', 'pipe']
  });
  
  let hasOutput = false;
  let timer = setTimeout(() => {
    console.log('❌ Test timeout (5s)');
    child.kill();
    runNextTest();
  }, 5000);
  
  child.stdout.on('data', (data) => {
    hasOutput = true;
    console.log('✅ stdout:', data.toString().trim());
    
    // Try to send a simple message
    try {
      const testMessage = {
        jsonrpc: '2.0',
        id: 1,
        method: 'initialize',
        params: {
          protocolVersion: '2024-11-05',
          capabilities: { tools: {} },
          clientInfo: { name: 'debug-client', version: '1.0.0' }
        }
      };
      child.stdin.write(JSON.stringify(testMessage) + '\n');
    } catch (e) {
      console.log('⚠️ Could not send test message:', e.message);
    }
  });
  
  child.stderr.on('data', (data) => {
    hasOutput = true;
    console.log('🔧 stderr:', data.toString().trim());
  });
  
  child.on('close', (code) => {
    clearTimeout(timer);
    console.log(`📊 Process exited with code: ${code}`);
    if (hasOutput) {
      console.log('✅ Got response from server');
    } else {
      console.log('❌ No response from server');
    }
    runNextTest();
  });
}

function runNextTest() {
  currentTestIndex++;
  if (currentTestIndex < tests.length) {
    setTimeout(() => runTest(tests[currentTestIndex]), 1000);
  } else {
    console.log('\n📋 Diagnosis Complete');
    process.exit(0);
  }
}

// Start testing
runTest(tests[currentTestIndex]); 