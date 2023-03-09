#include <iostream>
#include <string>
// #include <spdlog/spdlog.h>
// #include <socket>
// #include <json>
// #include <type_traits>
// #include <requests>
// #include <chrono>

// // Define the conversion function
// int map_log_level(std::string level_str) {
//     if (std::isdigit(level_str[0])) {
//         return std::stoi(level_str);
//     } else if (std::isalpha(level_str[0])) {
//         std::string level_name = level_str;
//         std::transform(level_name.begin(), level_name.end(), level_name.begin(), ::toupper);
//         try {
//             return logging.getLevelName(level_name);
//         } catch (const std::invalid_argument& e) {
//             throw std::invalid_argument("Invalid logging level: " + level_str);
//         }
//     } else {
//         throw std::invalid_argument("Invalid logging level: " + level_str);
//     }
// }

int main(int argc, char* argv[]) {
    // argparse::ArgumentParser parser("program description");
    // parser.add_argument("--ws-port", "Set the web socket server port to recieve messages from.", argparse::default_value<int>(6565), "int");
    // parser.add_argument("--ws-host", "Set the web socket server hostname to recieve messages from.", argparse::default_value<std::string>("localhost"), "string");
    // parser.add_argument("--port", "Set the web server server port to send commands too.", argparse::default_value<int>(5565), "int");
    // parser.add_argument("--host", "Set the web server server hostname. to send commands too", argparse::default_value<std::string>("localhost"), "string");
    // parser.add_argument("--log-level", "Set the logging level by integer value or string representation.", argparse::default_value<int>(logging.INFO), "int", map_log_level);
    // parser.add_argument("--azimuth-dp", "Set how many decimal places the azimuth is taken too.", argparse::default_value<int>(2), "int");
    // parser.add_argument("--elevation-dp", "Set how many decimal places the elevation is taken too.", argparse::default_value<int>(2), "int");
    // parser.add_argument("--delay","-d", "Delay to limit the data flow into the websocket server.", argparse::default_value<int>(0), "int");
    // parser.add_argument("--test","-t", "For testing it will not send requests to the driver.", "bool");
    // parser.add_argument("--speed","-s", "Set the speed factor o multiply the speed", argparse::default_value<float>(0.28), "float");
    // parser.add_argument("--smoothing","-sm", "The amount of smoothing factor for speed to optimal position", argparse::default_value<float>(1), "float");

    // parser.add_argument("--target-padding", "-p", "Set the padding for when the gun will try and shoot relative to the edge of the target in %. The amount of padding around the target bounding box in pixels that the gun will ignore before shooting", argparse::default_value<int>(10), "int");
    // parser.add_argument("--accuracy-threshold", "-th", "The threshold of how accurate the gun will try to get the target in the center of the crosshair in pixels.", argparse::default_value<int>(45), "int");


}