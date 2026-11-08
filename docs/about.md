# Author & Company

<div class="sfs-brand" markdown>

![SystemFromScratch® logo](assets/images/brand/systemfromscratch-logo-on-dark.png){ .sfs-brand__logo }

</div>

SmartManipulator-X is designed, written and maintained by **Anton Vynohradov** and
published by **SystemFromScratch®** — secure embedded systems and compliance-ready
engineering, from concept to certification.

## Author

<div class="sfs-author" markdown>

**Anton Vynohradov** · [ORCID 0009-0005-6965-0911](https://orcid.org/0009-0005-6965-0911)
{ .sfs-author__name }

Embedded Systems Engineer · Secure Product Architect · Founder of SystemFromScratch®
{ .sfs-author__role }

*Embedded systems built from scratch — from bare metal to Linux, from first schematic to
certification.*

</div>

Anton designs and builds reliable, secure embedded products end to end: firmware, board
support packages and drivers, RTOS and Embedded Linux platforms, hardware bring-up, and
the security and compliance work needed to ship them. He is based in Poland and works
remotely worldwide.

| Area | Focus |
| --- | --- |
| Embedded software | Bare-metal, RTOS and Linux firmware in C/C++, built to be maintained for years |
| BSP & drivers | Bootloaders, Zephyr drivers and Linux kernel work for MCUs, SoCs and SoC FPGAs |
| Security & compliance | Secure boot, threat modelling, MISRA C/C++, EU Cyber Resilience Act (CRA) readiness |
| Industries | Industrial IoT, automotive, robotics, medical and consumer electronics |

**Technology:** C · C++ · Python · Zephyr RTOS · FreeRTOS · Embedded Linux · Yocto ·
Buildroot · ARM Cortex-M · STM32 · Microchip FPGA · RISC-V · CAN / ISO-TP · ROS 2 ·
Docker · Git · CI/CD · MISRA C/C++ · EU CRA

For SmartManipulator-X, Anton designed the system architecture, the Robot PC image and
its ROS 2 configuration, the robot description generated from the BCN3D Moveo CAD, the
SmartFusion2 controller firmware with its motor tester, and this documentation.

## SystemFromScratch®

SystemFromScratch® was founded by Anton Vynohradov. The company combines deep embedded
engineering with cybersecurity and certification-focused product development, for teams
in industrial IoT, automotive, robotics, medical and consumer electronics that need a
partner who understands the whole stack — silicon, firmware, operating system and the
regulations that govern them.

| Service | What it covers |
| --- | --- |
| Embedded software development | Bare-metal, RTOS and Linux firmware for performance, reliability and long-term maintainability |
| BSP & device drivers | Board support packages, bootloaders and low-level drivers for MCUs, SoCs, FPGAs and custom hardware |
| RTOS & Embedded Linux | Zephyr, FreeRTOS and Embedded Linux (Yocto, Buildroot): porting, configuration, integration, reproducible builds |
| Hardware bring-up & integration | Schematic review, first boot, validation and production support, including SoC FPGA and motor-control platforms |
| Cybersecurity & CRA readiness | Secure boot, firmware integrity, threat modelling and a secure development lifecycle for the EU Cyber Resilience Act |
| Compliance & consulting | MISRA C/C++, static analysis, code and architecture reviews, compliance roadmaps |

SmartManipulator-X is one of the open-source projects in the SystemFromScratch®
portfolio: public engineering work that can be inspected line by line, from the ROS 2
host down to the stepper driver.

## Contact

| Channel | Address |
| --- | --- |
| Website | [systemfromscratch.com](https://systemfromscratch.com) |
| E-mail | [avynohradov@systemfromscratch.com](mailto:avynohradov@systemfromscratch.com) |
| GitHub | [github.com/AntonVynohradov](https://github.com/AntonVynohradov) |
| GitHub organization | [github.com/SystemFromScratch](https://github.com/SystemFromScratch) |
| LinkedIn | [linkedin.com/in/vynohradov](https://www.linkedin.com/in/vynohradov) |
| ORCID | [0009-0005-6965-0911](https://orcid.org/0009-0005-6965-0911) |
| Location | Poland — working remotely worldwide |

Building a robot, bringing up new hardware, or preparing for the Cyber Resilience Act?
Get in touch through [systemfromscratch.com](https://systemfromscratch.com) or by e-mail.

## Support and feedback

- **Bugs and feature requests:** open an issue on
  [GitHub](https://github.com/SystemFromScratch/sfs-smartmanipulator-x-robot/issues).
  Please include the repository commit, the host OS and Docker version, the command you
  ran and its output; for hardware, the firmware variant and the wiring revision.
- **Contributions:** read [Development](development.md) first; keep the documentation
  in step with the change.
- **Commercial support, integration and custom development:** contact SystemFromScratch®
  through [systemfromscratch.com](https://systemfromscratch.com).

## Trademarks and acknowledgements

SystemFromScratch® is a registered trademark. The SystemFromScratch® name and logo are used
in this documentation to identify the publisher of SmartManipulator-X; the Apache License
2.0 grants no rights to use them, and they may not be used to endorse or promote products
derived from SmartManipulator-X without prior written permission.

ROBOTIS, DYNAMIXEL and OpenMANIPULATOR are trademarks of ROBOTIS Co., Ltd. SmartFusion2
and Libero are trademarks of Microchip Technology Inc. TRINAMIC and TMC5160 are
trademarks of Analog Devices, Inc. BIGTREETECH is a trademark of Shenzhen Big Tree
Technology Co., Ltd. ROS is a trademark of Open Source Robotics Foundation, Inc. BCN3D is
a trademark of BCN3D Technologies. SmartManipulator-X is not affiliated with or endorsed
by these companies; their names are used only to identify the products the project
builds on.

The mechanical design comes from the
[BCN3D Moveo](https://github.com/BCN3D/BCN3D-Moveo) project (MIT license; the license
text ships with the robot description meshes). The ROS 2 software concepts come from
ROBOTIS [OpenMANIPULATOR-X](https://github.com/ROBOTIS-GIT/open_manipulator) and the
DYNAMIXEL SDK and hardware interface.
