//https://github.com/mqttjs/MQTT.js/issues/264
var mqtt    = require('mqtt');
const fs = require('fs');
const process = require('node:process');
console.log("process id is " + process.pid);
process.title = 'node-modelController';
global.childArray = []


//process.stdin.resume();

/*
var cleanExit = function() { 
  process.exit; 
};
  
process.on('SIGINT', cleanExit); // catch ctrl-c
process.on('SIGTERM', cleanExit);
process.on('uncaughtException', cleanExit);
process.on('SIGUSR1', cleanExit);
process.on('SIGUSR2', cleanExit);
process.on('exit', cleanExit);*/

  
  function instanceCheck(instanceId){
    const fs = require('fs');
    // directory to check if exists
    const dir = './instancesData/' + instanceId;
    // check if directory exists
    if (fs.existsSync(dir)) {
    return true;
    } else {
    return false;
    }
  }
  
  
  function stendModelStart(msgArgs, cmdInstance){

    // Check msg for data
    try{      
      if (!msgArgs.hasOwnProperty("InitialData")){
        throw new ReferenceError("Incomplete arg data: no InitialData is detected");
      }
      else{
        if (!msgArgs.InitialData.hasOwnProperty("stateVar")){
          throw new ReferenceError("Incomplete arg data: no stateVar is detected");
        }
        else{var stateVar = msgArgs.InitialData.stateVar;};
      };
      
      if (!msgArgs.hasOwnProperty("SystemInputs")){
        throw new ReferenceError("Incomplete arg data: no Vgas is detected");
      }
      else{
        if (!msgArgs.SystemInputs.hasOwnProperty("Kp_pid")){
          throw new ReferenceError("Incomplete arg data: no Twater_in is detected");
        }
        else{var Kp_pid = msgArgs.SystemInputs.Kp_pid;};

        if (!msgArgs.SystemInputs.hasOwnProperty("Ki_pid")){
          throw new ReferenceError("Incomplete arg data: no Twater_in is detected");
        }
        else{var Ki_pid = msgArgs.SystemInputs.Ki_pid;};

        if (!msgArgs.SystemInputs.hasOwnProperty("Kd_pid")){
          throw new ReferenceError("Incomplete arg data: no Twater_in is detected");
        }
        else{var Kd_pid = msgArgs.SystemInputs.Kd_pid;};
  
        if (!msgArgs.SystemInputs.hasOwnProperty("setpoint")){
          throw new ReferenceError("Incomplete arg data: no Duration is detected");
        }
        else{var setpoint = msgArgs.SystemInputs.setpoint;};
      };
    } catch(error) {
      console.error(error.message);
    };

    
    try{
      const fs = require('fs');
      const dir = './instancesData/' + cmdInstance+ "/initialData.json";
      const fileH = fs.openSync(dir, 'r');
      const rawdata = fs.readFileSync(fileH);
      let configDat = JSON.parse(rawdata);

      modelFile = configDat.modelID;
      fs.closeSync(fileH);
      console.log("ModelId: ",modelFile);
    } catch(error){
      console.log("Configuration file issues for model data");
      return (-1)
    }
    
    stendModelStop(cmdInstance)

    var spawn = require('child_process').spawn;
    var model = spawn('python3', [modelFile,cmdInstance, Kp_pid, Ki_pid, Kd_pid, setpoint, stateVar]);
    
    
    // model.stdout.on('data', function(data) {
    //   console.log(data.toString());
    // });
    // model.stdout.on('end', function(data) {
    //   console.log("end:",(data));
    //   });
    // model.stdout.on("close", function(data) {
    //   console.log("close:", (data));
    // });
    model.on('spawn', function() {
      console.log(`Child process PID: ${model.pid}`);
      global.childArray.push({"cmdInstance":cmdInstance,"pid":model.pid})
    });
    model.on('close', (code) => {
      console.log(`child process ${model.pid} exited with code ${code}`);
    });
    model.stderr.on('data', (data) => {
      console.error(`stderr: ${data}`);
    });
  };

  function stendModelStop(cmdInstance){
    global.childArray.forEach(FindId);

    function FindId(value, index, array) {
      if(value.cmdInstance.trim() === cmdInstance.trim()){
        process.kill(value.pid)
        console.log(value.cmdInstance,value.pid, 'proc were killed')
        array.splice(index,1)
      }
    }
  }

  function commandReak(msg){
    var logger = [];
    var result = 0;
    // Check if it is destination controller
    //!msgArgs.hasOwnProperty(
    try {
      if (!msg.hasOwnProperty("command")){
        throw new SyntaxError("Incomplete data: no destination command founded");
      };
      if (!msg.hasOwnProperty("object")){
        throw new SyntaxError("Incomplete data: no destination object founded");
      };
      if (!msg.command.type){
        throw new SyntaxError("Incomplete data: no command detected");
      }
      else{var cmdType = msg.command.type; logger.push([Date.now(), "Command detected"]);};
      
      if (!msg.object.hasOwnProperty("instance")){
        throw new SyntaxError("Incomplete data: no instance unic id detected");
      }
      else{var cmdInstance = msg.object.instance; logger.push([Date.now(), "Instance unic id detected"]);};
      
      /*
      if (!msg.command.hasOwnProperty("id")){
        throw new SyntaxError("Incomplete data: no command unic id detected");
      }
      else{var cmdId = msg.command.id; logger.push([Date.now(), "Command unic id detected"]);};
      */

      if (!msg.hasOwnProperty("args")){
        throw new SyntaxError("Incomplete data: no arguments are detected");
      }
      else{var msgArgs = msg.args; logger.push([Date.now(), "Arguments are detected"]);};

      console.log ("obj: ",cmdInstance," command: ",cmdType)

      // Check if command == add_instance

      switch(cmdType){
        case 'add_instance':
          if (!instanceCheck(cmdInstance)){

            result = 1;

          } else{
            throw new SyntaxError("Incorrect data: instance with current id exist");
          }
        break;

        // Check if command != add_instance
        default:
          if (instanceCheck(cmdInstance)){
            // Select command and check args
            switch(cmdType){
              case 'start': //STATIC
                  stendModelStart(msgArgs, cmdInstance);
                  result = 1;
              break;
                  
              case 'stop':
                  stendModelStop(cmdInstance);
                  result = 1;
              break;


              // case 'compute_dynamic':
              //     DynamicCompute(msgArgs, cmdInstance, cmdId);
              //     result = 1;
              // break;

              // case 'RTsim_start':
              //     RTCompute(msgArgs, cmdInstance, cmdId);
              //     result = 1;
              // break;

              default:
                throw new SyntaxError("Incorrect data: command `" + cmdType + "` in unknown");
            }

          } else{
            throw new SyntaxError("Incorrect data: instance with current id don`t exist");
          }
        };
  
  
    } catch (error) {
      console.log(err.message);
      logger.push([Date.now(), err.message]);
      result = -1;
    }
    
  return [result, logger]
  };

//read config data from json file 
// Define options for mqtt
const clientId = `mqtt_${Math.random().toString(16).slice(3)}`;
try {
    let rawdata = fs.readFileSync("config.json");
    let configDat = JSON.parse(rawdata);
    //var cert="ca.crt";

    var caFile =fs.readFileSync(configDat.mqttConfig.caFile, 'utf8');
    //if using client certificates
    var SEQ = configDat.mqttConfig.sequre;
    var HOST = "mqtt://" + configDat.mqttConfig.host;
    var topic = configDat.mqttConfig.topicCMD;
    var contrId = configDat.controller.id;

    if (SEQ) {

      var HOST = "mqtts://" + configDat.mqttConfig.host;
      var KEY = fs.readFileSync(configDat.mqttConfig.keyFile, 'utf8');
      var CERT = fs.readFileSync(configDat.mqttConfig.certFile, 'utf8');
      var options={
        clientId,
        port: configDat.mqttConfig.port,
        rejectUnauthorized : false,
        key: KEY,
        cert: CERT,
        username:configDat.mqttConfig.username,
        password:configDat.mqttConfig.password,
        ca:caFile 
      }
    }
    else{
      var options={
        clientId: clientId,
        port: configDat.mqttConfig.port,
        username:configDat.mqttConfig.username,
        password:configDat.mqttConfig.password,
        rejectUnauthorized : false
      }
    }
    console.log(HOST, options)
    
    
}catch(error){
    console.log("Configuration file issues");
    process.exit(1);
}

var client  = mqtt.connect(HOST,options);
console.log("connected flag  " + client.connected);
client.on("connect",function(){
    console.log('Connected')
    client.subscribe([topic], () => {
        console.log(`Subscribe to topic '${topic}'`);
    })
})
client.on("error",function(error){
    console.log("Can't connect" + error);
    //process.exit(1)
});
client.on('message', function onMsg (topic, payload) {
    var msg_log = [];
    try {
      var command = JSON.parse(payload.toString())
      console.log('Received Message:', topic, payload.toString())
    } catch (error) {
      console.log('Can not read JSON')
    }
    if (command){
    const res = commandReak(command,contrId);
    console.log(res.toString())
    }
  });
  