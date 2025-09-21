# Simulador do Algoritmo Paxos

## 📖 Visão Geral

Este é um simulador completo do algoritmo de consenso Paxos implementado em Python. O Paxos é um algoritmo fundamental em sistemas distribuídos usado para alcançar consenso entre múltiplos nós em uma rede, mesmo na presença de falhas e mensagens perdidas.

### O que é o Paxos?

O algoritmo Paxos resolve o problema do consenso distribuído, onde múltiplos nós precisam concordar sobre um único valor. Ele garante que:
- **Segurança**: Apenas um valor pode ser escolhido
- **Progresso**: Se a maioria dos nós está funcionando, um valor será eventualmente escolhido
- **Tolerância a falhas**: Funciona mesmo com falhas de nós (até N/2 falhas para N nós)

## 🏗️ Como Funciona o Algoritmo

O Paxos opera em duas fases principais com quatro tipos de mensagens:

### Fase 1: Preparação
1. **PREPARE** (1a): Proposer envia uma proposta com ID único para todos os acceptors
2. **PROMISE** (1b): Acceptors prometem não aceitar propostas com ID menor

### Fase 2: Aceitação
3. **ACCEPT** (2a): Proposer envia o valor para ser aceito pelos acceptors
4. **ACCEPTED** (2b): Acceptors aceitam o valor e notificam learners

### Papéis dos Nós
- **Proposer**: Inicia propostas
- **Acceptor**: Vota nas propostas
- **Learner**: Aprende o valor consensual

*Cada nó neste simulador pode desempenhar todos os três papéis simultaneamente.*

## 🚀 Instalação e Requisitos

### Requisitos
- Python 3.6 ou superior
- Bibliotecas padrão do Python (nenhuma dependência externa)

### Como Executar
```bash
# Clone ou baixe o arquivo paxos.py
python3 paxos.py
```

## 🎮 Como Usar o Simulador

### Menu Principal

Ao executar o simulador, você verá o seguinte menu:

```
🎛️  Paxos Simulation Menu
========================================
1. Create node          # Criar novo nó
2. Add proposal         # Adicionar proposta
3. Run simulation       # Executar simulação
4. Show network status  # Mostrar status da rede
5. Create test scenario # Criar cenário de teste
6. Exit                 # Sair
```

### Opções do Menu

#### 1. Create node (Criar nó)
Cria um novo nó na rede com um ID único.
```
Exemplo:
Enter node ID: node1
✅ Node 'node1' created successfully
```

#### 2. Add proposal (Adicionar proposta)
Adiciona uma proposta que será executada por um nó específico.
```
Exemplo:
📋 Available nodes: ['node1', 'node2', 'node3']
Enter proposer node ID: node1
Enter proposal value: valor_importante
✅ Proposal 'valor_importante' added for node 'node1'
```

#### 3. Run simulation (Executar simulação)
Executa todas as propostas pendentes simultaneamente e mostra o processo completo.

#### 4. Show network status (Mostrar status da rede)
Exibe informações sobre todos os nós e os valores que aprenderam.

#### 5. Create test scenario (Criar cenário de teste)
Cria automaticamente um cenário com 3 nós e 3 propostas concorrentes para demonstração.

#### 6. Exit (Sair)
Encerra o simulador.

## 📝 Exemplo de Uso Completo

### Cenário Básico
```
1. Escolha opção 1 → Digite "node1"
2. Escolha opção 1 → Digite "node2" 
3. Escolha opção 1 → Digite "node3"
4. Escolha opção 2 → Digite "node1" → Digite "minha_proposta"
5. Escolha opção 3 → Observe o algoritmo em ação!
```

### Cenário com Múltiplas Propostas Concorrentes
```
1. Escolha opção 5 (Create test scenario)
2. Escolha opção 3 (Run simulation)
3. Observe como o Paxos resolve o conflito e escolhe um valor
```

## 🔍 Exemplo de Saída

Quando você executa uma simulação, verá algo assim:

```
🚀 Starting Paxos simulation...
==================================================

📤 Node node0 proposing value 'value_A' with ID 1758494123789683
📥 Node node1 received PREPARE from node0 for proposal 1758494123789683
✅ Node node1 promised to proposal 1758494123789683
📥 Node node0 received PROMISE from node1 for proposal 1758494123789683
📊 Node node0 has 2/3 promises (need 2)
📤 Node node0 sent ACCEPT with value: 'value_A'
✅ Node node1 accepted proposal 1758494123789683 with value: 'value_A'
🎉 Node node0 learned CONSENSUS: Proposal 1758494123789683 = 'value_A'
```

## 🏛️ Estrutura do Código

### Classes Principais

#### `MessageType` (Enum)
Define os 4 tipos de mensagens do Paxos:
- `PREPARE` - Fase 1a
- `PROMISE` - Fase 1b  
- `ACCEPT` - Fase 2a
- `ACCEPTED` - Fase 2b

#### `Message` (Dataclass)
Representa uma mensagem entre nós contendo:
- Tipo da mensagem
- ID da proposta
- ID do remetente e destinatário
- Valor proposto
- Informações sobre valores aceitos anteriormente

#### `Network`
Simula a rede de comunicação:
- Gerencia todos os nós
- Simula atrasos de rede (0.1s por padrão)
- Implementa broadcast e envio direcionado

#### `PaxosNode`
Implementa um nó Paxos completo com métodos refinados:
- `propose()` - Inicia uma nova proposta
- `ReceiveProposeSendPromise()` - Processa PREPARE, envia PROMISE
- `ReceivePromiseSendAccept()` - Processa PROMISE, envia ACCEPT
- `ReceiveAcceptSendAccepted()` - Processa ACCEPT, envia ACCEPTED
- `handle_accepted()` - Processa ACCEPTED, detecta consenso

#### `PaxosSimulation`
Coordena a simulação:
- Cria e gerencia nós
- Agenda propostas
- Executa simulações com threading

## ⚙️ Características Técnicas

### IDs de Proposta Únicos
- Usa timestamps com precisão de microssegundos
- Garante unicidade mesmo em propostas simultâneas
- Formato: `int(time.time() * 1000000)`

### Detecção de Maioria
- Calcula threshold como `len(nodes) // 2 + 1`
- Funciona com qualquer número ímpar de nós
- Recomendado: mínimo 3 nós para demonstrar consenso

### Threading e Concorrência
- Propostas simultâneas usando threads
- Atrasos escalonados para simular concorrência real
- Thread-safe com locks onde necessário

### Logging Detalhado
- Emojis para facilitar identificação visual
- Rastreamento completo do fluxo de mensagens
- Contadores de votos e detecção de consenso

## 🧪 Cenários de Teste Recomendados

### Teste 1: Proposta Única
- 3 nós, 1 proposta
- Deve alcançar consenso rapidamente

### Teste 2: Propostas Concorrentes  
- 3 nós, 3 propostas simultâneas
- Observar como o Paxos escolhe uma proposta

### Teste 3: Rede Maior
- 5-7 nós, múltiplas propostas
- Testar escalabilidade

### Teste 4: Valores Diferentes
- Propor valores com tipos diferentes (strings, números)
- Verificar handling genérico

## 🔧 Personalização

### Ajustar Atrasos de Rede
```python
network.message_delay = 0.5  # 500ms de atraso
```

### Modificar Threshold de Maioria
```python
# No método relevante, altere:
majority_threshold = len(self.network.nodes) // 2 + 1
```

## 📚 Conceitos Importantes

### Propriedades de Segurança
- **Validade**: Apenas valores propostos podem ser escolhidos
- **Acordo**: Nós não podem decidir valores diferentes
- **Terminação**: Se a maioria funciona, uma decisão será tomada

### Tratamento de Conflitos
- Propostas com ID maior têm prioridade
- Valores previamente aceitos são preservados
- Sistema de promessas evita interferências

## 🐛 Resolução de Problemas

### Problema: "No pending proposals"
**Solução**: Adicione propostas antes de executar simulação (opção 2)

### Problema: "Create nodes first!"
**Solução**: Crie pelo menos um nó antes de adicionar propostas (opção 1)

### Problema: Nenhum consenso alcançado
**Verificações**:
- Tem pelo menos 3 nós?
- Aguardou tempo suficiente (3+ segundos)?
- Verifique logs para entender o fluxo

## 📖 Referências

- [Paxos Made Simple - Leslie Lamport](https://lamport.azurewebsites.net/pubs/paxos-simple.pdf)
- [The Part-Time Parliament - Leslie Lamport](https://lamport.azurewebsites.net/pubs/lamport-paxos.pdf)
