// WebSocket连接管理
class WebSocketManager {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
    }

    connect() {
        try {
            console.log('正在连接WebSocket服务器...');
            console.log('WebSocket服务器地址:', 'ws://localhost:8765');
            
            // 尝试创建WebSocket对象
            console.log('尝试创建WebSocket对象...');
            this.socket = new WebSocket('ws://localhost:8765');
            console.log('WebSocket对象创建成功:', this.socket);
            
            this.socket.onopen = () => {
                console.log('WebSocket连接成功');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.onConnect();
            };
            
            this.socket.onmessage = (event) => {
                console.log('收到消息:', event.data);
                this.onMessage(event.data);
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket错误:', error);
                this.isConnected = false;
                this.attemptReconnect();
            };
            
            this.socket.onclose = () => {
                console.log('WebSocket连接关闭');
                this.isConnected = false;
                this.attemptReconnect();
            };
        } catch (error) {
            console.error('WebSocket连接失败:', error);
            console.error('错误堆栈:', error.stack);
            this.attemptReconnect();
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`尝试重连... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay);
        } else {
            console.error('WebSocket重连失败，已达到最大尝试次数');
        }
    }

    async send(message) {
        try {
            if (this.isConnected && this.socket.readyState === WebSocket.OPEN) {
                this.socket.send(JSON.stringify(message));
                console.log('消息发送成功');
                return true;
            } else {
                console.error('WebSocket未连接，无法发送消息');
                return false;
            }
        } catch (error) {
            console.error('发送消息失败:', error);
            return false;
        }
    }

    close() {
        if (this.socket) {
            this.socket.close();
        }
    }

    // 回调函数
    onConnect() {}
    onMessage(data) {}
}

// 聊天应用
class ChatApp {
    constructor() {
        this.wsManager = new WebSocketManager();
        this.sessionId = 'test_session_123';
        this.init();
    }

    init() {
        // 初始化WebSocket连接
        this.wsManager.onConnect = () => {
            this.updateStatus('已连接');
        };

        this.wsManager.onMessage = (data) => {
            try {
                const message = JSON.parse(data);
                this.handleMessage(message);
            } catch (error) {
                console.error('解析消息失败:', error);
            }
        };

        // 连接WebSocket
        this.wsManager.connect();

        // 绑定事件
        this.bindEvents();
        
        // 添加键盘快捷键
        this.bindKeyboardShortcuts();
    }
    
    bindKeyboardShortcuts() {
        // 全局键盘事件监听
        document.addEventListener('keydown', (e) => {
            // Alt+S 打开设置面板
            if (e.altKey && e.key === 's') {
                e.preventDefault();
                console.log('Alt+S 快捷键触发');
                this.openSettings();
            }
        });
        console.log('已绑定键盘快捷键 Alt+S');
    }

    bindEvents() {
        // 保存当前实例的引用
        const self = this;
        
        console.log('开始绑定事件...');
        
        // 延迟绑定事件，确保DOM完全加载
        setTimeout(() => {
            console.log('开始绑定按钮事件...');
            
            // 创建工作区按钮
            const createWorkspaceButton = document.querySelector('.create-workspace');
            console.log('创建工作区按钮元素:', createWorkspaceButton);
            if (createWorkspaceButton) {
                createWorkspaceButton.addEventListener('click', function() {
                    console.log('点击创建工作区按钮');
                    self.createWorkspace();
                });
                console.log('已绑定创建工作区按钮事件');
            } else {
                console.error('未找到创建工作区按钮');
            }

            // 发送按钮点击事件
            const sendButton = document.querySelector('.send-button');
            console.log('发送按钮元素:', sendButton);
            if (sendButton) {
                sendButton.addEventListener('click', async function() {
                    console.log('点击发送按钮');
                    await self.sendMessage();
                });
                console.log('已绑定发送按钮事件');
            } else {
                console.error('未找到发送按钮');
            }

            // 输入框回车事件
            const messageInput = document.getElementById('messageInput');
            console.log('消息输入框元素:', messageInput);
            if (messageInput) {
                messageInput.addEventListener('keypress', async function(e) {
                    if (e.key === 'Enter') {
                        console.log('输入框回车，发送消息');
                        await self.sendMessage();
                    }
                });
                console.log('已绑定输入框回车事件');
            } else {
                console.error('未找到消息输入框');
            }

            // 工作区切换
            const workspaceItems = document.querySelectorAll('.workspace-item');
            console.log('找到工作区项目数量:', workspaceItems.length);
            workspaceItems.forEach(item => {
                item.addEventListener('click', function() {
                    console.log('点击工作区:', item.querySelector('.workspace-name').textContent);
                    self.switchWorkspace(item);
                });
            });

            // 会话切换
            const sessionItems = document.querySelectorAll('.session-item');
            console.log('找到会话项目数量:', sessionItems.length);
            sessionItems.forEach(item => {
                item.addEventListener('click', function() {
                    console.log('点击会话:', item.querySelector('.session-name').textContent);
                    self.switchSession(item);
                });
            });

            // 保存设置
            const saveButton = document.querySelector('.save-settings');
            console.log('保存设置按钮元素:', saveButton);
            if (saveButton) {
                saveButton.addEventListener('click', function() {
                    console.log('点击保存设置按钮');
                    self.saveSettings();
                });
                console.log('已绑定保存设置按钮事件');
            } else {
                console.error('未找到保存设置按钮');
            }

            // 通道配置按钮
            const configureButtons = document.querySelectorAll('.configure-channel');
            console.log('找到通道配置按钮数量:', configureButtons.length);
            configureButtons.forEach(button => {
                console.log('绑定通道配置按钮事件:', button);
                button.addEventListener('click', function() {
                    console.log('点击了配置按钮');
                    const channelItem = this.closest('.channel-item');
                    console.log('通道项:', channelItem);
                    if (channelItem) {
                        const channelName = channelItem.querySelector('.channel-name').textContent;
                        console.log('点击配置通道按钮:', channelName);
                        self.configureChannel(channelName);
                    } else {
                        console.error('未找到通道项');
                    }
                });
            });
            
            // 聊天头部设置按钮
            const settingsButton = document.getElementById('settingsButton');
            console.log('设置按钮元素:', settingsButton);
            if (settingsButton) {
                console.log('设置按钮的outerHTML:', settingsButton.outerHTML);
                console.log('设置按钮的style:', window.getComputedStyle(settingsButton));
                console.log('设置按钮的offsetParent:', settingsButton.offsetParent);
                console.log('设置按钮的clientWidth:', settingsButton.clientWidth);
                console.log('设置按钮的clientHeight:', settingsButton.clientHeight);
                console.log('设置按钮的getBoundingClientRect():', settingsButton.getBoundingClientRect());
                
                // 重置所有事件监听器
                settingsButton.onclick = null;
                
                // 添加简单的点击事件
                settingsButton.addEventListener('click', function(e) {
                    console.log('点击设置按钮');
                    console.log('事件对象:', e);
                    console.log('事件目标:', e.target);
                    console.log('this指向:', this);
                    self.openSettings();
                });
                console.log('已绑定设置按钮事件');
            } else {
                console.error('未找到设置按钮');
            }
            
            // 添加事件委托到body，捕获所有点击事件
            document.body.addEventListener('click', function(e) {
                console.log('body捕获点击事件');
                console.log('点击目标:', e.target);
                console.log('点击目标ID:', e.target.id);
                
                // 如果点击的是设置按钮
                if (e.target.id === 'settingsButton' || e.target.closest('#settingsButton')) {
                    console.log('通过事件委托捕获到设置按钮点击');
                    self.openSettings();
                }
            }, true); // 使用捕获阶段
            console.log('已添加事件委托到body');
            
            // 检查chat-actions区域的点击事件
            const chatActions = document.querySelector('.chat-actions');
            if (chatActions) {
                chatActions.addEventListener('click', function(e) {
                    console.log('chat-actions捕获点击事件');
                    console.log('点击目标:', e.target);
                }, true);
                console.log('已添加chat-actions点击事件监听');
            }
            
            console.log('事件绑定完成');
        }, 100);
    }

    configureChannel(channelName) {
        console.log('配置通道:', channelName);
        
        // 显示配置模态框
        this.showChannelConfigModal(channelName);
    }
    
    showChannelConfigModal(channelName) {
        // 创建配置模态框
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.id = 'channelConfigModal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>配置 ${channelName} 通道</h3>
                    <button id="closeChannelModal" class="btn btn-secondary">×</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label for="channelUrl">通道URL</label>
                        <input type="text" id="channelUrl" class="form-input" placeholder="请输入通道URL">
                    </div>
                    <div class="form-group">
                        <label for="channelToken">通道令牌</label>
                        <input type="text" id="channelToken" class="form-input" placeholder="请输入通道令牌">
                    </div>
                    <div class="form-group">
                        <label for="channelEnabled">是否启用</label>
                        <select id="channelEnabled" class="form-select">
                            <option value="true">启用</option>
                            <option value="false">禁用</option>
                        </select>
                    </div>
                </div>
                <div class="modal-footer">
                    <button id="cancelChannelConfig" class="btn btn-secondary">取消</button>
                    <button id="saveChannelConfig" class="btn btn-primary">保存配置</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        modal.style.display = 'block';
        console.log('显示通道配置模态框:', channelName);
        
        // 绑定模态框按钮事件
        const self = this;
        
        // 关闭按钮
        document.getElementById('closeChannelModal').onclick = function() {
            self.hideChannelConfigModal();
        };
        
        // 取消按钮
        document.getElementById('cancelChannelConfig').onclick = function() {
            self.hideChannelConfigModal();
        };
        
        // 保存配置按钮
        document.getElementById('saveChannelConfig').onclick = async function() {
            await self.saveChannelConfig(channelName);
        };
        
        // 点击模态框外部关闭
        window.onclick = function(event) {
            if (event.target == modal) {
                self.hideChannelConfigModal();
            }
        };
    }
    
    hideChannelConfigModal() {
        const modal = document.getElementById('channelConfigModal');
        if (modal) {
            modal.style.display = 'none';
            document.body.removeChild(modal);
            console.log('隐藏通道配置模态框');
        }
    }
    
    async saveChannelConfig(channelName) {
        const channelUrl = document.getElementById('channelUrl').value;
        const channelToken = document.getElementById('channelToken').value;
        const channelEnabled = document.getElementById('channelEnabled').value === 'true';
        
        // 创建通道配置对象
        const config = {
            url: channelUrl,
            token: channelToken,
            enabled: channelEnabled
        };
        
        console.log('保存通道配置:', channelName, config);
        
        // 发送通道配置请求
        const channelConfigMessage = {
            type: 'channel_config',
            channel_name: channelName,
            config: config
        };
        
        if (await this.wsManager.send(channelConfigMessage)) {
            console.log('通道配置请求发送成功');
            this.hideChannelConfigModal();
        } else {
            console.error('通道配置请求发送失败');
            alert('通道配置请求发送失败，请检查WebSocket连接');
        }
    }

    async runSelfTest() {
        console.log('开始运行系统自测');
        
        // 显示加载状态
        const resultsDiv = document.getElementById('selfTestResults');
        if (resultsDiv) {
            resultsDiv.innerHTML = '<p>正在运行自测...</p>';
        }
        
        // 发送自测请求
        const selfTestMessage = {
            type: 'self_test'
        };
        
        console.log('发送自测请求:', selfTestMessage);
        
        if (await this.wsManager.send(selfTestMessage)) {
            console.log('自测请求发送成功');
        } else {
            console.error('自测请求发送失败');
            if (resultsDiv) {
                resultsDiv.innerHTML = '<p class="test-item fail">自测请求发送失败，请检查WebSocket连接</p>';
            }
        }
    }

    handleSelfTestResponse(results) {
        console.log('收到自测结果:', results);
        
        const resultsDiv = document.getElementById('selfTestResults');
        if (resultsDiv) {
            let html = `<h4>自测结果: ${results.overall === 'pass' ? '通过' : '失败'}</h4>`;
            
            // 连接测试
            html += `<div class="test-item ${results.connection_test}">
                连接测试: ${results.connection_test === 'pass' ? '通过' : '失败'}
                <div class="test-details">${results.details.connection_test}</div>
            </div>`;
            
            // 消息处理测试
            html += `<div class="test-item ${results.message_test}">
                消息处理测试: ${results.message_test === 'pass' ? '通过' : '失败'}
                <div class="test-details">${results.details.message_test}</div>
            </div>`;
            
            // 通道配置测试
            html += `<div class="test-item ${results.channel_test}">
                通道配置测试: ${results.channel_test === 'pass' ? '通过' : '失败'}
                <div class="test-details">${results.details.channel_test}</div>
            </div>`;
            
            // 性能测试
            html += `<div class="test-item ${results.performance_test}">
                性能测试: ${results.performance_test === 'pass' ? '通过' : '失败'}
                <div class="test-details">${results.details.performance_test}</div>
            </div>`;
            
            resultsDiv.innerHTML = html;
        }
    }

    async sendMessage() {
        const input = document.getElementById('messageInput');
        const content = input.value.trim();

        if (content) {
            // 创建消息对象，确保格式与后端一致
            const message = {
                type: 'message',
                session_id: this.sessionId,
                content: content,
                msg_id: this.generateMessageId()
            };

            console.log('发送消息:', message);
            
            // 发送消息
            if (await this.wsManager.send(message)) {
                // 显示本地消息
                this.addMessage('你', content, new Date().toLocaleTimeString());
                // 清空输入框
                input.value = '';
            } else {
                console.error('消息发送失败');
            }
        }
    }

    handleMessage(message) {
        if (message.type === 'message' && message.session_id === this.sessionId) {
            // 显示AI消息
            this.addMessage('AI', message.content, new Date().toLocaleTimeString(), true);
        } else if (message.type === 'pong') {
            console.log('收到pong响应');
        } else if (message.type === 'self_test_response') {
            // 处理自测响应
            console.log('收到自测响应:', message);
            this.handleSelfTestResponse(message.results);
        } else if (message.type === 'channel_config_response') {
            // 处理通道配置响应
            console.log('收到通道配置响应:', message);
            alert(message.message);
        } else if (message.type === 'channel_status_response') {
            // 处理通道状态响应
            console.log('收到通道状态响应:', message);
        } else if (message.type === 'wechat_connect_response') {
            // 处理微信连接响应
            console.log('收到微信连接响应:', message);
            if (message.status === 'success') {
                console.log('微信账号连接成功');
                // 更新微信通道状态
                this.updateWechatChannelStatus('已连接');
                // 切换到微信通道
                this.switchChannel('wechat');
            } else {
                console.error('微信账号连接失败:', message.message);
                alert('微信账号连接失败: ' + message.message);
            }
        } else if (message.type === 'sms_send_code_response') {
            // 处理SMS验证码发送响应
            console.log('收到SMS验证码发送响应:', message);
            if (message.status === 'success') {
                console.log('验证码发送成功:', message.verification_code);
                // 显示验证码（仅用于测试，实际项目中不应显示）
                alert('验证码已发送，测试验证码: ' + message.verification_code);
            } else {
                console.error('验证码发送失败:', message.message);
                alert('验证码发送失败: ' + message.message);
            }
        } else if (message.type === 'sms_connect_response') {
            // 处理SMS通道连接响应
            console.log('收到SMS通道连接响应:', message);
            if (message.status === 'success') {
                console.log('SMS通道连接成功');
                // 更新SMS通道状态
                this.updateSmsChannelStatus('已连接');
                // 切换到SMS通道
                this.switchChannel('sms');
            } else {
                console.error('SMS通道连接失败:', message.message);
                alert('SMS通道连接失败: ' + message.message);
            }
        } else if (message.type === 'email_send_code_response') {
            // 处理Email验证码发送响应
            console.log('收到Email验证码发送响应:', message);
            if (message.status === 'success') {
                console.log('验证码发送成功:', message.verification_code);
                // 显示验证码（仅用于测试，实际项目中不应显示）
                alert('验证码已发送，测试验证码: ' + message.verification_code);
            } else {
                console.error('验证码发送失败:', message.message);
                alert('验证码发送失败: ' + message.message);
            }
        } else if (message.type === 'email_connect_response') {
            // 处理Email通道连接响应
            console.log('收到Email通道连接响应:', message);
            if (message.status === 'success') {
                console.log('Email通道连接成功');
                // 更新Email通道状态
                this.updateEmailChannelStatus('已连接');
                // 切换到Email通道
                this.switchChannel('email');
            } else {
                console.error('Email通道连接失败:', message.message);
                alert('Email通道连接失败: ' + message.message);
            }
        }
    }

    addMessage(sender, content, time, isAI = false) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isAI ? 'ai-message' : ''}`;

        const avatar = isAI ? '🤖' : '👤';
        
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-sender">${sender}</span>
                    <span class="message-time">${time}</span>
                </div>
                <div class="message-text">${content}</div>
            </div>
        `;

        messagesContainer.appendChild(messageDiv);
        // 滚动到底部
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    switchWorkspace(item) {
        // 移除所有工作区的活动状态
        document.querySelectorAll('.workspace-item').forEach(i => i.classList.remove('active'));
        // 添加当前工作区的活动状态
        item.classList.add('active');
        // 更新工作区名称
        const workspaceName = item.querySelector('.workspace-name').textContent;
        document.querySelector('.chat-title').textContent = workspaceName;
    }

    switchSession(item) {
        // 移除所有会话的活动状态
        document.querySelectorAll('.session-item').forEach(i => i.classList.remove('active'));
        // 添加当前会话的活动状态
        item.classList.add('active');
        // 更新会话名称
        const sessionName = item.querySelector('.session-name').textContent;
        document.querySelector('.chat-title').textContent = sessionName;
        // 这里可以添加加载会话历史的逻辑
    }

    switchChannel(channelName) {
        console.log('切换通道:', channelName);
        
        // 移除所有通道服务项的活动状态
        document.querySelectorAll('.channel-service-item').forEach(item => item.classList.remove('active'));
        
        // 找到并激活当前通道
        const channelItems = document.querySelectorAll('.channel-service-item');
        for (const item of channelItems) {
            if (item.querySelector('.channel-service-name').textContent === channelName || 
                (channelName === 'wechat' && item.querySelector('.channel-service-name').textContent === '微信') ||
                (channelName === 'discord' && item.querySelector('.channel-service-name').textContent === 'Discord') ||
                (channelName === 'slack' && item.querySelector('.channel-service-name').textContent === 'Slack') ||
                (channelName === 'telegram' && item.querySelector('.channel-service-name').textContent === 'Telegram') ||
                (channelName === 'sms' && item.querySelector('.channel-service-name').textContent === 'SMS') ||
                (channelName === 'email' && item.querySelector('.channel-service-name').textContent === 'Email')) {
                item.classList.add('active');
                break;
            }
        }
        
        // 发送通道切换请求到后端
        const channelSwitchMessage = {
            type: 'channel_switch',
            channel_name: channelName
        };
        
        this.wsManager.send(channelSwitchMessage).then(success => {
            if (success) {
                console.log('通道切换请求发送成功');
            } else {
                console.error('通道切换请求发送失败');
            }
        });
        
        // 更新聊天标题以显示当前通道
        let displayName = channelName;
        switch(channelName) {
            case 'wechat':
                displayName = '微信';
                break;
            case 'discord':
                displayName = 'Discord';
                break;
            case 'slack':
                displayName = 'Slack';
                break;
            case 'telegram':
                displayName = 'Telegram';
                break;
            case 'sms':
                displayName = 'SMS';
                break;
            case 'email':
                displayName = 'Email';
                break;
        }
        document.querySelector('.chat-title').textContent = displayName + ' 通道';
    }

    saveSettings() {
        const workspaceName = document.querySelector('.setting-input').value;
        const workspaceIcon = document.querySelector('.setting-select').value;
        
        // 更新工作区名称和图标
        const activeWorkspace = document.querySelector('.workspace-item.active');
        if (activeWorkspace) {
            activeWorkspace.querySelector('.workspace-icon').textContent = workspaceIcon;
            activeWorkspace.querySelector('.workspace-name').textContent = workspaceName;
        }

        // 显示保存成功提示
        alert('设置已保存');
    }

    updateStatus(status) {
        document.querySelector('.chat-status').textContent = status;
    }

    generateMessageId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    createWorkspace() {
        console.log('开始创建工作区');
        try {
            // 显示模态框
            this.showCreateWorkspaceModal();
        } catch (error) {
            console.error('创建工作区失败:', error);
        }
    }

    showCreateWorkspaceModal() {
        const modal = document.getElementById('createWorkspaceModal');
        if (modal) {
            modal.style.display = 'block';
            console.log('显示工作区创建模态框');
            
            // 绑定模态框按钮事件
            const self = this;
            
            // 关闭按钮
            document.getElementById('closeModal').onclick = function() {
                self.hideCreateWorkspaceModal();
            };
            
            // 取消按钮
            document.getElementById('cancelCreate').onclick = function() {
                self.hideCreateWorkspaceModal();
            };
            
            // 确认创建按钮
            document.getElementById('confirmCreate').onclick = function() {
                self.confirmCreateWorkspace();
            };
            
            // 点击模态框外部关闭
            window.onclick = function(event) {
                if (event.target == modal) {
                    self.hideCreateWorkspaceModal();
                }
            };
        } else {
            console.error('未找到工作区创建模态框');
        }
    }

    hideCreateWorkspaceModal() {
        const modal = document.getElementById('createWorkspaceModal');
        if (modal) {
            modal.style.display = 'none';
            console.log('隐藏工作区创建模态框');
        }
    }

    confirmCreateWorkspace() {
        const workspaceNameInput = document.getElementById('workspaceName');
        const workspaceIconSelect = document.getElementById('workspaceIcon');
        
        if (workspaceNameInput && workspaceIconSelect) {
            const workspaceName = workspaceNameInput.value.trim();
            const workspaceIcon = workspaceIconSelect.value;
            
            if (workspaceName) {
                console.log('用户输入工作区名称:', workspaceName);
                console.log('用户选择工作区图标:', workspaceIcon);
                
                // 创建新的工作区元素
                const workspaceItems = document.querySelector('.workspace-items');
                if (workspaceItems) {
                    const newWorkspace = document.createElement('li');
                    newWorkspace.className = 'workspace-item';
                    
                    newWorkspace.innerHTML = `
                        <div class="workspace-icon">${workspaceIcon}</div>
                        <span class="workspace-name">${workspaceName}</span>
                    `;
                    
                    // 添加到工作区列表
                    workspaceItems.appendChild(newWorkspace);
                    console.log('已添加新工作区:', workspaceName);
                    
                    // 绑定点击事件
                    const self = this;
                    newWorkspace.addEventListener('click', function() {
                        self.switchWorkspace(newWorkspace);
                    });
                    
                    // 切换到新工作区
                    this.switchWorkspace(newWorkspace);
                    
                    // 隐藏模态框
                    this.hideCreateWorkspaceModal();
                    
                    // 清空输入
                    workspaceNameInput.value = '';
                } else {
                    console.error('未找到工作区列表');
                }
            } else {
                alert('请输入工作区名称');
            }
        } else {
            console.error('未找到工作区名称输入框或图标选择框');
        }
    }

    openSettings() {
        console.log('打开设置面板');
        // 显示一个alert，确认方法被调用
        alert('设置按钮被点击！');
        // 滚动到右侧信息面板的设置部分
        const infoPanel = document.querySelector('.info-panel');
        if (infoPanel) {
            infoPanel.scrollTop = 0;
            console.log('已滚动到设置面板顶部');
        }
    }

    // 打开微信账号连接模态框
    openWechatConnectModal() {
        console.log('打开微信账号连接模态框');
        const modal = document.getElementById('wechatConnectModal');
        if (modal) {
            modal.style.display = 'block';
            console.log('显示微信账号连接模态框');
            
            // 绑定模态框按钮事件
            const self = this;
            
            // 关闭按钮
            document.getElementById('closeWechatModal').onclick = function() {
                self.hideWechatConnectModal();
            };
            
            // 取消按钮
            document.getElementById('cancelWechatConnect').onclick = function() {
                self.hideWechatConnectModal();
            };
            
            // 连接按钮
            document.getElementById('confirmWechatConnect').onclick = function() {
                self.connectWechatAccount();
            };
            
            // 点击模态框外部关闭
            window.onclick = function(event) {
                if (event.target == modal) {
                    self.hideWechatConnectModal();
                }
            };
            
            // 生成微信登录二维码（模拟）
            this.generateWechatQRCode();
        } else {
            console.error('未找到微信账号连接模态框');
        }
    }

    // 隐藏微信账号连接模态框
    hideWechatConnectModal() {
        const modal = document.getElementById('wechatConnectModal');
        if (modal) {
            modal.style.display = 'none';
            console.log('隐藏微信账号连接模态框');
        }
    }

    // 生成微信登录二维码（模拟）
    generateWechatQRCode() {
        console.log('生成微信登录二维码');
        const statusElement = document.getElementById('wechatLoginStatus');
        if (statusElement) {
            statusElement.textContent = '正在生成二维码...';
        }
        
        // 模拟二维码生成过程
        setTimeout(() => {
            const qrCodeElement = document.getElementById('wechatQRCode');
            if (qrCodeElement) {
                qrCodeElement.innerHTML = `
                    <div style="font-size: 48px;">📱</div>
                    <p>请使用微信扫码登录</p>
                    <p id="wechatLoginStatus" style="color: #48bb78;">二维码已生成，请扫码</p>
                    <div style="margin-top: 20px; font-size: 12px; color: #718096;">模拟二维码: WECHAT_LOGIN_123456</div>
                `;
            }
        }, 1000);
    }

    // 连接微信账号
    async connectWechatAccount() {
        console.log('连接微信账号');
        const accountType = document.getElementById('wechatAccountType').value;
        
        console.log('微信账号类型:', accountType);
        
        // 模拟微信登录过程
        const statusElement = document.getElementById('wechatLoginStatus');
        if (statusElement) {
            statusElement.textContent = '正在登录...';
        }
        
        // 模拟登录延迟
        setTimeout(async () => {
            // 发送微信连接请求到后端
            const wechatConnectMessage = {
                type: 'wechat_connect',
                account_type: accountType,
                action: 'connect'
            };
            
            if (await this.wsManager.send(wechatConnectMessage)) {
                console.log('微信连接请求发送成功');
                if (statusElement) {
                    statusElement.textContent = '登录成功！';
                }
                
                // 延迟关闭模态框
                setTimeout(() => {
                    this.hideWechatConnectModal();
                    // 更新微信通道状态
                    this.updateWechatChannelStatus('已连接');
                }, 1000);
            } else {
                console.error('微信连接请求发送失败');
                if (statusElement) {
                    statusElement.textContent = '登录失败，请重试';
                }
            }
        }, 2000);
    }

    // 更新微信通道状态
    updateWechatChannelStatus(status) {
        console.log('更新微信通道状态:', status);
        const wechatChannelItem = document.querySelector('.channel-item .channel-name');
        if (wechatChannelItem && wechatChannelItem.textContent === '微信') {
            const statusElement = wechatChannelItem.nextElementSibling;
            if (statusElement) {
                statusElement.textContent = status;
                if (status === '已连接') {
                    statusElement.classList.add('active');
                } else {
                    statusElement.classList.remove('active');
                }
            }
        }
    }

    // 打开SMS通道连接模态框
    openSmsConnectModal() {
        console.log('打开SMS通道连接模态框');
        const modal = document.getElementById('smsConnectModal');
        if (modal) {
            modal.style.display = 'block';
            console.log('显示SMS通道连接模态框');
            
            // 绑定模态框按钮事件
            const self = this;
            
            // 关闭按钮
            document.getElementById('closeSmsModal').onclick = function() {
                self.hideSmsConnectModal();
            };
            
            // 取消按钮
            document.getElementById('cancelSmsConnect').onclick = function() {
                self.hideSmsConnectModal();
            };
            
            // 连接按钮
            document.getElementById('confirmSmsConnect').onclick = function() {
                self.connectSmsChannel();
            };
            
            // 点击模态框外部关闭
            window.onclick = function(event) {
                if (event.target == modal) {
                    self.hideSmsConnectModal();
                }
            };
        } else {
            console.error('未找到SMS通道连接模态框');
        }
    }

    // 隐藏SMS通道连接模态框
    hideSmsConnectModal() {
        const modal = document.getElementById('smsConnectModal');
        if (modal) {
            modal.style.display = 'none';
            console.log('隐藏SMS通道连接模态框');
        }
    }

    // 发送SMS验证码
    async sendSmsVerificationCode() {
        console.log('发送SMS验证码');
        const phoneNumber = document.getElementById('smsPhoneNumber').value;
        const serviceProvider = document.getElementById('smsServiceProvider').value;
        
        if (!phoneNumber) {
            alert('请输入手机号码');
            return;
        }
        
        console.log('手机号码:', phoneNumber);
        console.log('服务提供商:', serviceProvider);
        
        // 禁用发送按钮
        const sendButton = document.getElementById('sendSmsCode');
        sendButton.disabled = true;
        sendButton.textContent = '发送中...';
        
        // 发送验证码请求到后端
        const smsCodeMessage = {
            type: 'sms_send_code',
            phone_number: phoneNumber,
            service_provider: serviceProvider
        };
        
        if (await this.wsManager.send(smsCodeMessage)) {
            console.log('发送验证码请求成功');
            // 倒计时
            let countdown = 60;
            sendButton.textContent = `${countdown}秒后重发`;
            
            const timer = setInterval(() => {
                countdown--;
                sendButton.textContent = `${countdown}秒后重发`;
                if (countdown <= 0) {
                    clearInterval(timer);
                    sendButton.disabled = false;
                    sendButton.textContent = '发送验证码';
                }
            }, 1000);
        } else {
            console.error('发送验证码请求失败');
            sendButton.disabled = false;
            sendButton.textContent = '发送验证码';
            alert('发送验证码失败，请重试');
        }
    }

    // 连接SMS通道
    async connectSmsChannel() {
        console.log('连接SMS通道');
        const phoneNumber = document.getElementById('smsPhoneNumber').value;
        const verificationCode = document.getElementById('smsVerificationCode').value;
        const serviceProvider = document.getElementById('smsServiceProvider').value;
        
        if (!phoneNumber) {
            alert('请输入手机号码');
            return;
        }
        
        if (!verificationCode) {
            alert('请输入验证码');
            return;
        }
        
        console.log('手机号码:', phoneNumber);
        console.log('验证码:', verificationCode);
        console.log('服务提供商:', serviceProvider);
        
        // 发送SMS连接请求到后端
        const smsConnectMessage = {
            type: 'sms_connect',
            phone_number: phoneNumber,
            verification_code: verificationCode,
            service_provider: serviceProvider
        };
        
        if (await this.wsManager.send(smsConnectMessage)) {
            console.log('SMS连接请求发送成功');
            // 显示连接成功提示
            alert('SMS通道连接成功！');
            // 隐藏模态框
            this.hideSmsConnectModal();
            // 更新SMS通道状态
            this.updateSmsChannelStatus('已连接');
            // 切换到SMS通道
            this.switchChannel('sms');
        } else {
            console.error('SMS连接请求发送失败');
            alert('SMS通道连接失败，请重试');
        }
    }

    // 更新SMS通道状态
    updateSmsChannelStatus(status) {
        console.log('更新SMS通道状态:', status);
        const channelItems = document.querySelectorAll('.channel-item .channel-name');
        for (const item of channelItems) {
            if (item.textContent === 'SMS') {
                const statusElement = item.nextElementSibling;
                if (statusElement) {
                    statusElement.textContent = status;
                    if (status === '已连接') {
                        statusElement.classList.add('active');
                    } else {
                        statusElement.classList.remove('active');
                    }
                }
                break;
            }
        }
    }

    // 打开Email通道连接模态框
    openEmailConnectModal() {
        console.log('打开Email通道连接模态框');
        const modal = document.getElementById('emailConnectModal');
        if (modal) {
            modal.style.display = 'block';
            console.log('显示Email通道连接模态框');
            
            // 绑定模态框按钮事件
            const self = this;
            
            // 关闭按钮
            document.getElementById('closeEmailModal').onclick = function() {
                self.hideEmailConnectModal();
            };
            
            // 取消按钮
            document.getElementById('cancelEmailConnect').onclick = function() {
                self.hideEmailConnectModal();
            };
            
            // 连接按钮
            document.getElementById('confirmEmailConnect').onclick = function() {
                self.connectEmailChannel();
            };
            
            // 点击模态框外部关闭
            window.onclick = function(event) {
                if (event.target == modal) {
                    self.hideEmailConnectModal();
                }
            };
        } else {
            console.error('未找到Email通道连接模态框');
        }
    }

    // 隐藏Email通道连接模态框
    hideEmailConnectModal() {
        const modal = document.getElementById('emailConnectModal');
        if (modal) {
            modal.style.display = 'none';
            console.log('隐藏Email通道连接模态框');
        }
    }

    // 发送Email验证码
    async sendEmailVerificationCode() {
        console.log('发送Email验证码');
        const emailAddress = document.getElementById('emailAddress').value;
        const serviceProvider = document.getElementById('emailServiceProvider').value;
        
        if (!emailAddress) {
            alert('请输入邮箱地址');
            return;
        }
        
        console.log('邮箱地址:', emailAddress);
        console.log('服务提供商:', serviceProvider);
        
        // 禁用发送按钮
        const sendButton = document.getElementById('sendEmailCode');
        sendButton.disabled = true;
        sendButton.textContent = '发送中...';
        
        // 发送验证码请求到后端
        const emailCodeMessage = {
            type: 'email_send_code',
            email_address: emailAddress,
            service_provider: serviceProvider
        };
        
        if (await this.wsManager.send(emailCodeMessage)) {
            console.log('发送验证码请求成功');
            // 倒计时
            let countdown = 60;
            sendButton.textContent = `${countdown}秒后重发`;
            
            const timer = setInterval(() => {
                countdown--;
                sendButton.textContent = `${countdown}秒后重发`;
                if (countdown <= 0) {
                    clearInterval(timer);
                    sendButton.disabled = false;
                    sendButton.textContent = '发送验证码';
                }
            }, 1000);
        } else {
            console.error('发送验证码请求失败');
            sendButton.disabled = false;
            sendButton.textContent = '发送验证码';
            alert('发送验证码失败，请重试');
        }
    }

    // 连接Email通道
    async connectEmailChannel() {
        console.log('连接Email通道');
        const emailAddress = document.getElementById('emailAddress').value;
        const verificationCode = document.getElementById('emailVerificationCode').value;
        const serviceProvider = document.getElementById('emailServiceProvider').value;
        
        if (!emailAddress) {
            alert('请输入邮箱地址');
            return;
        }
        
        if (!verificationCode) {
            alert('请输入验证码');
            return;
        }
        
        console.log('邮箱地址:', emailAddress);
        console.log('验证码:', verificationCode);
        console.log('服务提供商:', serviceProvider);
        
        // 发送Email连接请求到后端
        const emailConnectMessage = {
            type: 'email_connect',
            email_address: emailAddress,
            verification_code: verificationCode,
            service_provider: serviceProvider
        };
        
        if (await this.wsManager.send(emailConnectMessage)) {
            console.log('Email连接请求发送成功');
            // 显示连接成功提示
            alert('Email通道连接成功！');
            // 隐藏模态框
            this.hideEmailConnectModal();
            // 更新Email通道状态
            this.updateEmailChannelStatus('已连接');
            // 切换到Email通道
            this.switchChannel('email');
        } else {
            console.error('Email连接请求发送失败');
            alert('Email通道连接失败，请重试');
        }
    }

    // 更新Email通道状态
    updateEmailChannelStatus(status) {
        console.log('更新Email通道状态:', status);
        const channelItems = document.querySelectorAll('.channel-item .channel-name');
        for (const item of channelItems) {
            if (item.textContent === 'Email') {
                const statusElement = item.nextElementSibling;
                if (statusElement) {
                    statusElement.textContent = status;
                    if (status === '已连接') {
                        statusElement.classList.add('active');
                    } else {
                        statusElement.classList.remove('active');
                    }
                }
                break;
            }
        }
    }
}

// 全局设置按钮点击处理函数
function handleSettingsClick() {
    console.log('全局handleSettingsClick函数触发');
    if (window.chatApp) {
        console.log('调用window.chatApp.openSettings()');
        window.chatApp.openSettings();
    } else {
        console.error('window.chatApp不存在');
    }
}

// 全局mousedown事件监听器
document.addEventListener('mousedown', function(e) {
    console.log('全局mousedown事件捕获');
    console.log('点击目标:', e.target);
    console.log('点击目标ID:', e.target.id);
    
    if (e.target.id === 'settingsButton') {
        console.log('mousedown事件捕获到设置按钮');
        e.preventDefault();
        if (window.chatApp) {
            window.chatApp.openSettings();
        }
    }
}, true);

// 全局点击事件监听器，用于调试
document.addEventListener('click', function(e) {
    console.log('全局点击事件捕获');
    console.log('点击目标:', e.target);
    console.log('点击目标ID:', e.target.id);
    console.log('点击目标类名:', e.target.className);
    console.log('事件类型:', e.type);
    console.log('事件冒泡阶段:', e.eventPhase);
    console.log('事件是否可取消:', e.cancelable);
    console.log('事件是否已阻止默认行为:', e.defaultPrevented);
    console.log('事件是否已阻止冒泡:', e.bubbles);
}, true); // 使用捕获阶段

// 使用jQuery绑定设置按钮的点击事件
$(document).ready(function() {
    console.log('jQuery文档就绪');
    
    // 绑定设置按钮的点击事件
    $('#settingsButton').on('click', function() {
        console.log('jQuery点击事件触发');
        if (window.chatApp) {
            window.chatApp.openSettings();
        }
    });
    
    // 绑定设置按钮的mousedown事件
    $('#settingsButton').on('mousedown', function() {
        console.log('jQuery mousedown事件触发');
        if (window.chatApp) {
            window.chatApp.openSettings();
        }
    });
    
    console.log('已通过jQuery绑定设置按钮事件');
});

// 使用setInterval定期检查设置按钮
const checkSettingsButton = setInterval(function() {
    const settingsButton = document.getElementById('settingsButton');
    if (settingsButton) {
        console.log('setInterval发现设置按钮:', settingsButton);
        
        // 绑定点击事件
        settingsButton.addEventListener('click', function() {
            console.log('设置按钮被点击 (setInterval绑定)');
            if (window.chatApp) {
                window.chatApp.openSettings();
            }
        });
        
        // 直接设置onclick属性
        settingsButton.onclick = function() {
            console.log('设置按钮被点击 (onclick属性)');
            if (window.chatApp) {
                window.chatApp.openSettings();
            }
        };
        
        console.log('已通过setInterval绑定设置按钮事件');
        
        // 停止检查
        clearInterval(checkSettingsButton);
    } else {
        console.log('setInterval未找到设置按钮');
    }
}, 1000); // 每秒检查一次
console.log('已启动setInterval定期检查设置按钮');

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    try {
        console.log('DOMContentLoaded事件触发');
        console.log('document.readyState:', document.readyState);
        
        // 全局点击事件监听器，直接在DOMContentLoaded中添加
        document.addEventListener('click', function(e) {
            console.log('全局点击事件捕获');
            console.log('点击目标:', e.target);
            console.log('点击目标ID:', e.target.id);
            
            // 检查是否点击了设置按钮
            if (e.target.id === 'settingsButton' || e.target.closest('#settingsButton')) {
                console.log('捕获到设置按钮点击');
                e.preventDefault();
                if (window.chatApp) {
                    console.log('调用window.chatApp.openSettings()');
                    window.chatApp.openSettings();
                } else {
                    console.error('window.chatApp不存在');
                }
            }
        }, true); // 使用捕获阶段
        console.log('已添加全局点击事件监听器');
        
        // 检查设置按钮是否存在
        const settingsButton = document.getElementById('settingsButton');
        console.log('设置按钮元素:', settingsButton);
        
        // 直接为设置按钮添加点击事件
        if (settingsButton) {
            settingsButton.onclick = function(e) {
                e.preventDefault();
                console.log('直接onclick属性触发');
                if (window.chatApp) {
                    window.chatApp.openSettings();
                }
            };
            console.log('已为设置按钮添加直接onclick属性');
        }
        
        window.chatApp = new ChatApp();
        console.log('ChatApp实例已暴露到window对象');
        console.log('ChatApp实例:', window.chatApp);
        console.log('configureChannel方法:', window.chatApp.configureChannel);
        console.log('openSettings方法:', window.chatApp.openSettings);
        
        // 测试openSettings方法
        console.log('测试openSettings方法...');
        window.chatApp.openSettings();
    } catch (error) {
        console.error('初始化ChatApp失败:', error);
        console.error('错误堆栈:', error.stack);
    }
});