/************************************************************************
Copyright (c) 2020, Unitree Robotics.Co.Ltd. All rights reserved.
Use of this source code is governed by the MPL-2.0 license, see LICENSE.
************************************************************************/

#include "unitree_legged_sdk/unitree_legged_sdk.h"
#include <math.h>
#include <iostream>
#include <unistd.h>
#include <string.h>
#include <fstream>
#include "multi_pc_type.h"
//#include<ctime>
//#include <chrono>
#include <stdio.h>
#include <string>

#include <arpa/inet.h>  // htons, inet_addr
#include <netinet/in.h> // sockaddr_in
#include <sys/types.h>  // uint16_t
#include <sys/socket.h> // socket, sendto
#include <unistd.h>     // close  

#define HOST "192.168.123.162"//"192.168.123.109"
#define PORT 3114


using namespace UNITREE_LEGGED_SDK;
//using namespace std::chrono;
#define timeStep 3000
class Custom
{
public:
    Custom(): control(LeggedType::A1, HIGHLEVEL), udp(){
        control.InitCmdData(cmd);
    }
    void UDPRecv();
    void UDPSend();
    void RobotControl();
    Control control;
    UDP udp;
    HighCmd cmd = {0};
    HighState state = {0};
    int motiontime = 0;
    float dt = 0.01;     // 0.001~0.01
    AAA a;
    BBB b;

    /*Custom Declaration*/
    //IMU Data from mainboard to laptop
    imuLineAcctoPC imuData={0};
    imuRPYtoPC imuAngle={0};
    imuGyrotoPC imuAnguSpeed = {0};

};


void Custom::UDPRecv()
{
    udp.Recv();
    // std::cout<<"udp recv"<<std::endl;
}

void Custom::UDPSend()
{  
    udp.Send();
    // std::cout<<"udp send"<<std::endl;
}

void Custom::RobotControl() 
{
    //std::time_t ts = std::time(0);
    // std::ofstream outfile;
    // outfile.open("motion.txt", std::ios_base::app); // append instead of overwrite
    //motiontime += dt*1000;
    //udp.GetRecv(state);
    // //printf("%d   %f\n", motiontime, state.forwardSpeed);
    // static int lastMotionTime = 0;
    // if (motiontime-lastMotionTime>10){
    //     outfile<<motiontime;
    //     outfile<<","<<state.forwardPosition;
    //     outfile<<","<<state.sidePosition;
    //     in/home/ywh/Development/unitree_sdk_jonathan/main/main.cppt i=0;
    //     for(i=0;i<4;i++) outfile<<","<< state.imu.quaternion[i];
    //     for(i=0;i<3;i++) outfile<<","<< state.imu.gyroscope[i];
    //     for(i=0;i<3;i++) outfile<<","<< state.imu.rpy[i];
    // for(i=0;i<3;i++) outfile<<","<< state.imu.accelerometer[i];
    //     outfile<<std::endl;
    //     lastMotionTime = motiontime;
    // }
    static long runCnt = 0;
    runCnt++;
    static int udpMissingCnt = 0;
    static float rxCmd[8] = {0.0};
    udp.GetRecv(state);   

    //Jonathan's version
    //UDP init
    int sock = ::socket(AF_INET, SOCK_DGRAM, 0);
    //std::cout<<"Socket status: "<<sock<<std::endl;
    struct sockaddr_in destination;
    memset(&destination, 0, sizeof(destination));  
    destination.sin_family = AF_INET;
    destination.sin_addr.s_addr = inet_addr(HOST); //INADDR_ANY;
    destination.sin_port = htons(PORT);
    int addrlen = sizeof(destination);
    //UDP TX timeout
    struct timeval tv;
    tv.tv_sec = 0;
    tv.tv_usec = 100000;
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

    static char tx_buf[1024], rx_buf[1024];
    //UDP TX
    int nn = sprintf(tx_buf, "{\"pos\":[%.08f,%.08f],\"rpy\":[%.08f,%.08f,%.08f],\"gyr\":[%.08f,%.08f,%.08f],\"acl\":[%.08f,%.08f,%.08f],\"qut\":[%.08f,%.08f,%.08f,%.08f]}", 
    state.forwardPosition, state.sidePosition, 
    state.imu.rpy[0], state.imu.rpy[1], state.imu.rpy[2],
    state.imu.gyroscope[0],state.imu.gyroscope[1],state.imu.gyroscope[2],
    state.imu.accelerometer[0],state.imu.accelerometer[1],state.imu.accelerometer[2],
    state.imu.quaternion[0],state.imu.quaternion[1],state.imu.quaternion[2],state.imu.quaternion[3]
    );
    int n_bytes = sendto(sock, tx_buf, nn, 0, (struct sockaddr *)&destination, sizeof(destination));
   // std::cout << n_bytes << " bytes sent\t";
    
    //UDP RX
    int n = recvfrom(sock, rx_buf, 1024, 0, (struct sockaddr *)&destination, (socklen_t *)&addrlen);
    ::close(sock);
    if (n>0)  rx_buf[n] = '\0';
    std::string rxStr;
    for(int i=0;i<n;i++) rxStr=rxStr+rx_buf[i];
    if (n<0){
        udpMissingCnt++;
    }
    else{
        udpMissingCnt = 0;
        //std::cout << "Rx msg:\t" << rxStr.length() << "\t :" << rxStr << std::endl;
        char *ptr;
        #define delimit ","
        ptr = strtok(rx_buf, delimit);
        int i=0;
        while(ptr != NULL){
            rxCmd[i] = atof(ptr);
            ptr = strtok(NULL, delimit);
            i++;
        }
        //At there data got
        cmd.mode = (int)rxCmd[0];
        cmd.forwardSpeed = rxCmd[1];
        cmd.sideSpeed = rxCmd[2];
        cmd.rotateSpeed = rxCmd[3];
        cmd.bodyHeight = rxCmd[4];
        cmd.roll  = rxCmd[5];
        cmd.pitch = rxCmd[6];
        cmd.yaw = rxCmd[7];
        // std::cout <<(int)cmd.mode<<'\t'<<cmd.forwardSpeed<<std::endl;
    }
    if(udpMissingCnt>3){ // Labtop controller disconnected. Stop the dog in auto
        cmd.mode = 1;
        cmd.forwardSpeed = 0.0f;
        cmd.sideSpeed = 0.0f;
        cmd.rotateSpeed = 0.0f;
        cmd.bodyHeight = 0.0f;

        cmd.roll  = 0;
        cmd.pitch = 0;
        cmd.yaw = 0;
        // std::cout << "NoRm"<<'\t'<<(int)cmd.mode<<'\t'<<udpMissingCnt << std::endl;
    }
    //sleep(0.5);  
    udp.SetSend(cmd);
}

int main(void) 
{
    std::cout << "HKUST ECE Jo-seph-gor's research group\n Developed by Jonathan Chan" << std::endl
              << "WARNING: Make sure the robot is standing on the ground." << std::endl
              << "Press Enter to continue..." << std::endl;
    std::cin.ignore();


    Custom custom; 

    LoopFunc loop_control("control_loop", custom.dt   , boost::bind(&Custom::RobotControl, &custom));
    LoopFunc loop_udpSend("udp_send",     custom.dt, 3, boost::bind(&Custom::UDPSend,      &custom));
    LoopFunc loop_udpRecv("udp_recv",     custom.dt, 3, boost::bind(&Custom::UDPRecv,      &custom));

    loop_udpSend.start();
    loop_udpRecv.start();
    loop_control.start();

    
    while (1)  
    {
       
        sleep(10);
    }

    

    return 0; 
}
