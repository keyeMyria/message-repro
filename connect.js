'use strict';

const WebSocket = require('ws');

function create() {
  const ws = new WebSocket('ws://localhost:8020/frontend/');

  ws.on('open', function open() {
    console.log('opened');

    ws.send(JSON.stringify({type: 'join', key: '1a'}));

    setTimeout(() => {
      ws.close();
    }, 1000);
  });

  ws.on('close', () => console.log('close'));
  ws.on('error', () => console.log('error'));
}

function create2() {
  create();
  create();
}

setInterval(create2, 500);
