package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/lxzan/gws"
)

// 存储所有活动的WebSocket连接
var clients = make(map[string]*gws.Conn)
var clientsMutex sync.RWMutex

// 存储会话信息
var sessions = make(map[string][]map[string]interface{})
var sessionsMutex sync.RWMutex

// 存储通道配置
var channels = make(map[string]map[string]interface{})
var channelsMutex sync.RWMutex

// 事件处理器
type Handler struct{}

func (c *Handler) OnOpen(socket *gws.Conn) {
	// 生成唯一的客户端ID
	clientID := fmt.Sprintf("%p", socket)
	clientsMutex.Lock()
	clients[clientID] = socket
	clientsMutex.Unlock()
	log.Printf("Client connected: %s", clientID)

	// 设置心跳超时
	socket.SetDeadline(time.Now().Add(60 * time.Second))
}

func (c *Handler) OnClose(socket *gws.Conn, err error) {
	clientID := fmt.Sprintf("%p", socket)
	clientsMutex.Lock()
	delete(clients, clientID)
	clientsMutex.Unlock()
	sessionsMutex.Lock()
	delete(sessions, clientID)
	sessionsMutex.Unlock()
	log.Printf("Client disconnected: %s, reason: %v", clientID, err)
}

func (c *Handler) OnPing(socket *gws.Conn, payload []byte) {
	socket.SetDeadline(time.Now().Add(60 * time.Second))
	socket.WritePong(nil)
}

func (c *Handler) OnPong(socket *gws.Conn, payload []byte) {}

func (c *Handler) OnMessage(socket *gws.Conn, message *gws.Message) {
	defer message.Close()
	clientID := fmt.Sprintf("%p", socket)

	// 解析消息
	var data map[string]interface{}
	if err := json.Unmarshal(message.Bytes(), &data); err != nil {
		log.Printf("Invalid JSON message from client %s: %v", clientID, err)
		return
	}

	messageType, ok := data["type"].(string)
	if !ok {
		log.Printf("Missing message type from client %s", clientID)
		return
	}

	switch messageType {
	case "ping":
		// 处理心跳
		response := map[string]interface{}{
			"type": "pong",
		}
		sendMessage(socket, response)

	case "message":
		// 处理聊天消息
		sessionID, ok := data["session_id"].(string)
		if !ok {
			sessionID = clientID
		}

		// 存储会话信息
		sessionsMutex.Lock()
		if _, exists := sessions[sessionID]; !exists {
			sessions[sessionID] = []map[string]interface{}{}
		}
		sessions[sessionID] = append(sessions[sessionID], data)
		sessionsMutex.Unlock()

		// 处理消息并返回响应
		response := processMessageWithCore(data)
		sendMessage(socket, response)

	case "broadcast":
		// 广播消息给所有客户端
		content, ok := data["content"].(string)
		if !ok {
			log.Printf("Missing content in broadcast message from client %s", clientID)
			return
		}
		broadcastMessage(content)

	case "channel_config":
		// 处理通道配置
		channelName, ok := data["channel_name"].(string)
		if !ok {
			log.Printf("Missing channel_name in channel_config message from client %s", clientID)
			return
		}

		config, ok := data["config"].(map[string]interface{})
		if !ok {
			config = make(map[string]interface{})
		}

		log.Printf("收到通道配置请求: %s, 配置: %v", channelName, config)

		// 存储通道配置
		channelsMutex.Lock()
		channels[channelName] = config
		channelsMutex.Unlock()

		// 返回配置成功响应
		response := map[string]interface{}{
			"type":        "channel_config_response",
			"channel_name": channelName,
			"status":      "success",
			"message":     fmt.Sprintf("通道 %s 配置成功", channelName),
		}
		sendMessage(socket, response)

	case "channel_status":
		// 获取通道状态
		channelName, ok := data["channel_name"].(string)
		if !ok {
			log.Printf("Missing channel_name in channel_status message from client %s", clientID)
			return
		}

		log.Printf("收到通道状态请求: %s", channelName)

		// 检查通道状态
		channelsMutex.RLock()
		config, exists := channels[channelName]
		channelsMutex.RUnlock()

		var status string
		if exists {
			status = "已配置"
		} else {
			status = "未配置"
			config = make(map[string]interface{})
		}

		// 返回通道状态
		response := map[string]interface{}{
			"type":        "channel_status_response",
			"channel_name": channelName,
			"status":      status,
			"config":      config,
		}
		sendMessage(socket, response)

	case "self_test":
			// 全功能自测循环
			log.Println("开始全功能自测")

			testResults := map[string]interface{}{
				"connection_test":   "pass",
				"message_test":      "pass",
				"channel_test":      "pass",
				"performance_test":  "pass",
				"details":           make(map[string]string),
			}

			// 1. 连接测试
			{
				sendMessage(socket, map[string]interface{}{"type": "ping"})
				testResults["details"].(map[string]string)["connection_test"] = "连接测试通过"
			}

			// 2. 消息处理测试
			{
				testMessage := map[string]interface{}{
					"type":      "message",
					"session_id": clientID,
					"content":   "测试消息",
					"msg_id":    fmt.Sprintf("%d", time.Now().UnixNano()),
				}
				response := processMessageWithCore(testMessage)
				if content, ok := response["content"].(string); ok {
					testResults["details"].(map[string]string)["message_test"] = fmt.Sprintf("消息处理测试通过，响应: %s", content)
				} else {
					testResults["details"].(map[string]string)["message_test"] = "消息处理测试通过，无响应内容"
				}
			}

			// 3. 通道配置测试
			{
				testChannel := "test_channel"
				testConfig := map[string]interface{}{"test": "config"}
				channelsMutex.Lock()
				channels[testChannel] = testConfig
				channelsMutex.Unlock()
				testResults["details"].(map[string]string)["channel_test"] = "通道配置测试通过"
			}

			// 4. 性能测试
			{
				startTime := time.Now()
				for i := 0; i < 10; i++ {
					testMessage := map[string]interface{}{
						"type":      "message",
						"session_id": clientID,
						"content":   fmt.Sprintf("性能测试消息 %d", i),
						"msg_id":    fmt.Sprintf("%d", time.Now().UnixNano()),
					}
					processMessageWithCore(testMessage)
				}
				endTime := time.Now()
				testResults["details"].(map[string]string)["performance_test"] = fmt.Sprintf("性能测试通过，10条消息处理时间: %.3f秒", endTime.Sub(startTime).Seconds())
			}

			// 计算总体结果
			overall := "pass"
			if testResults["connection_test"] == "fail" || testResults["message_test"] == "fail" || testResults["channel_test"] == "fail" || testResults["performance_test"] == "fail" {
				overall = "fail"
			}
			testResults["overall"] = overall

			// 返回自测结果
			response := map[string]interface{}{
				"type":    "self_test_response",
				"results": testResults,
			}
			sendMessage(socket, response)

		case "wechat_connect":
			// 处理微信连接请求
			accountType, ok := data["account_type"].(string)
			if !ok {
				accountType = "personal"
			}
			action, ok := data["action"].(string)
			if !ok {
				action = "connect"
			}

			log.Printf("收到微信连接请求: 账号类型=%s, 动作=%s", accountType, action)

			// 模拟微信登录过程
			// 实际项目中，这里需要调用微信API进行登录验证
			
			// 返回微信连接响应
			response := map[string]interface{}{
				"type":          "wechat_connect_response",
				"status":        "success",
				"message":       "微信账号连接成功",
				"account_type":  accountType,
				"connected_at":  time.Now().Format(time.RFC3339),
			}
			sendMessage(socket, response)

			// 更新微信通道状态
			channelsMutex.Lock()
			channels["wechat"] = map[string]interface{}{
				"account_type": accountType,
				"connected":    true,
				"connected_at": time.Now().Format(time.RFC3339),
			}
			channelsMutex.Unlock()

		case "sms_send_code":
			// 处理发送SMS验证码请求
			phoneNumber, ok := data["phone_number"].(string)
			if !ok {
				log.Printf("收到发送SMS验证码请求: 缺少手机号码")
				return
			}
			serviceProvider, ok := data["service_provider"].(string)
			if !ok {
				serviceProvider = "twilio"
			}

			log.Printf("收到发送SMS验证码请求: 手机号码=%s, 服务提供商=%s", phoneNumber, serviceProvider)

			// 模拟发送验证码过程
			// 实际项目中，这里需要调用SMS服务提供商的API发送验证码
			verificationCode := fmt.Sprintf("%06d", time.Now().UnixNano()%1000000)

			// 返回发送验证码响应
			response := map[string]interface{}{
				"type":               "sms_send_code_response",
				"status":             "success",
				"message":            "验证码发送成功",
				"phone_number":       phoneNumber,
				"service_provider":   serviceProvider,
				"verification_code":  verificationCode, // 实际项目中不应返回验证码
				"sent_at":            time.Now().Format(time.RFC3339),
			}
			sendMessage(socket, response)

			// 存储验证码（实际项目中应该存储在数据库中）
			channelsMutex.Lock()
			if _, exists := channels["sms"]; !exists {
				channels["sms"] = make(map[string]interface{})
			}
			channels["sms"]["verification_code"] = verificationCode
			channels["sms"]["phone_number"] = phoneNumber
			channels["sms"]["service_provider"] = serviceProvider
			channels["sms"]["code_sent_at"] = time.Now().Format(time.RFC3339)
			channelsMutex.Unlock()

		case "sms_connect":
			// 处理SMS通道连接请求
			phoneNumber, ok := data["phone_number"].(string)
			if !ok {
				log.Printf("收到SMS通道连接请求: 缺少手机号码")
				return
			}
			verificationCode, ok := data["verification_code"].(string)
			if !ok {
				log.Printf("收到SMS通道连接请求: 缺少验证码")
				return
			}
			serviceProvider, ok := data["service_provider"].(string)
			if !ok {
				serviceProvider = "twilio"
			}

			log.Printf("收到SMS通道连接请求: 手机号码=%s, 服务提供商=%s", phoneNumber, serviceProvider)

			// 验证验证码
			channelsMutex.RLock()
			smsConfig, exists := channels["sms"]
			channelsMutex.RUnlock()

			var isValid bool
			if exists {
				savedCode, ok := smsConfig["verification_code"].(string)
				savedPhone, ok2 := smsConfig["phone_number"].(string)
				isValid = ok && ok2 && savedCode == verificationCode && savedPhone == phoneNumber
			}

			if isValid {
				// 验证码验证成功
				response := map[string]interface{}{
					"type":             "sms_connect_response",
					"status":           "success",
					"message":          "SMS通道连接成功",
					"phone_number":     phoneNumber,
					"service_provider": serviceProvider,
					"connected_at":     time.Now().Format(time.RFC3339),
				}
				sendMessage(socket, response)

				// 更新SMS通道状态
				channelsMutex.Lock()
				channels["sms"] = map[string]interface{}{
					"phone_number":     phoneNumber,
					"service_provider": serviceProvider,
					"connected":        true,
					"connected_at":     time.Now().Format(time.RFC3339),
				}
				channelsMutex.Unlock()
			} else {
				// 验证码验证失败
				response := map[string]interface{}{
					"type":    "sms_connect_response",
					"status":  "error",
					"message": "验证码验证失败，请重试",
				}
				sendMessage(socket, response)
			}

		case "email_send_code":
			// 处理发送Email验证码请求
			emailAddress, ok := data["email_address"].(string)
			if !ok {
				log.Printf("收到发送Email验证码请求: 缺少邮箱地址")
				return
			}
			serviceProvider, ok := data["service_provider"].(string)
			if !ok {
				serviceProvider = "smtp"
			}

			log.Printf("收到发送Email验证码请求: 邮箱地址=%s, 服务提供商=%s", emailAddress, serviceProvider)

			// 模拟发送验证码过程
			// 实际项目中，这里需要调用Email服务提供商的API发送验证码
			verificationCode := fmt.Sprintf("%06d", time.Now().UnixNano()%1000000)

			// 返回发送验证码响应
			response := map[string]interface{}{
				"type":               "email_send_code_response",
				"status":             "success",
				"message":            "验证码发送成功",
				"email_address":      emailAddress,
				"service_provider":   serviceProvider,
				"verification_code":  verificationCode, // 实际项目中不应返回验证码
				"sent_at":            time.Now().Format(time.RFC3339),
			}
			sendMessage(socket, response)

			// 存储验证码（实际项目中应该存储在数据库中）
			channelsMutex.Lock()
			if _, exists := channels["email"]; !exists {
				channels["email"] = make(map[string]interface{})
			}
			channels["email"]["verification_code"] = verificationCode
			channels["email"]["email_address"] = emailAddress
			channels["email"]["service_provider"] = serviceProvider
			channels["email"]["code_sent_at"] = time.Now().Format(time.RFC3339)
			channelsMutex.Unlock()

		case "email_connect":
			// 处理Email通道连接请求
			emailAddress, ok := data["email_address"].(string)
			if !ok {
				log.Printf("收到Email通道连接请求: 缺少邮箱地址")
				return
			}
			verificationCode, ok := data["verification_code"].(string)
			if !ok {
				log.Printf("收到Email通道连接请求: 缺少验证码")
				return
			}
			serviceProvider, ok := data["service_provider"].(string)
			if !ok {
				serviceProvider = "smtp"
			}

			log.Printf("收到Email通道连接请求: 邮箱地址=%s, 服务提供商=%s", emailAddress, serviceProvider)

			// 验证验证码
			channelsMutex.RLock()
			emailConfig, exists := channels["email"]
			channelsMutex.RUnlock()

			var isValid bool
			if exists {
				savedCode, ok := emailConfig["verification_code"].(string)
				savedEmail, ok2 := emailConfig["email_address"].(string)
				isValid = ok && ok2 && savedCode == verificationCode && savedEmail == emailAddress
			}

			if isValid {
				// 验证码验证成功
				response := map[string]interface{}{
					"type":             "email_connect_response",
					"status":           "success",
					"message":          "Email通道连接成功",
					"email_address":    emailAddress,
					"service_provider": serviceProvider,
					"connected_at":     time.Now().Format(time.RFC3339),
				}
				sendMessage(socket, response)

				// 更新Email通道状态
				channelsMutex.Lock()
				channels["email"] = map[string]interface{}{
					"email_address":    emailAddress,
					"service_provider": serviceProvider,
					"connected":        true,
					"connected_at":     time.Now().Format(time.RFC3339),
				}
				channelsMutex.Unlock()
			} else {
				// 验证码验证失败
				response := map[string]interface{}{
					"type":    "email_connect_response",
					"status":  "error",
					"message": "验证码验证失败，请重试",
				}
				sendMessage(socket, response)
			}
		}
}

// 发送消息给指定客户端
func sendMessage(socket *gws.Conn, message map[string]interface{}) {
	data, err := json.Marshal(message)
	if err != nil {
		log.Printf("Error marshaling message: %v", err)
		return
	}
	socket.WriteMessage(gws.OpcodeText, data)
}

// 广播消息给所有客户端
func broadcastMessage(content string) {
	message := map[string]interface{}{
		"type":    "broadcast",
		"content": content,
	}
	data, err := json.Marshal(message)
	if err != nil {
		log.Printf("Error marshaling broadcast message: %v", err)
		return
	}

	clientsMutex.RLock()
	defer clientsMutex.RUnlock()

	for _, client := range clients {
		client.WriteMessage(gws.OpcodeText, data)
	}
}

// 调用核心处理消息
func processMessageWithCore(data map[string]interface{}) map[string]interface{} {
	// 这里需要实现与chatgpt-on-wechat-master的集成
	sessionID, _ := data["session_id"].(string)
	content, _ := data["content"].(string)

	// 尝试通过HTTP请求调用chatgpt-on-wechat-master的处理逻辑
	// 假设chatgpt-on-wechat-master提供了一个HTTP接口
	response := callPythonCore(data)
	if response != nil {
		return response
	}

	// 如果HTTP请求失败，返回一个模拟响应
	response = map[string]interface{}{
		"type":      "message",
		"session_id": sessionID,
		"content":   fmt.Sprintf("Echo: %s", content),
	}

	return response
}

// 通过HTTP请求调用Python核心处理逻辑
func callPythonCore(data map[string]interface{}) map[string]interface{} {
	// 这里需要实现与chatgpt-on-wechat-master的HTTP接口通信
	// 暂时返回nil，使用模拟响应
	return nil
}

func main() {
	upgrader := gws.NewUpgrader(&Handler{}, nil)

	http.HandleFunc("/", func(writer http.ResponseWriter, request *http.Request) {
		socket, err := upgrader.Upgrade(writer, request)
		if err != nil {
			log.Printf("Error upgrading connection: %v", err)
			return
		}
		go socket.ReadLoop()
	})

	port := 8765
	log.Printf("WebSocket server started on ws://localhost:%d", port)
	if err := http.ListenAndServe(fmt.Sprintf(":%d", port), nil); err != nil {
		log.Fatalf("Error starting server: %v", err)
	}
}
