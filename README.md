# Применение смарт-контрактов для координации робототехнических систем

**НИР по производственной практике**  
НИУ МЭИ, ИВТИ, кафедра ВМСС, направление 09.03.01 «Информатика и вычислительная техника»  
Студент: Поздняков Андрей Григорьевич, группа А-08-24  
Руководитель: Оцоков Шамиль Алиевич

---

## О чём проект

Демонстрация того, как несколько роботов без единого диспетчера распределяют между собой задания через **аукционный механизм на MQTT**, а итог аукциона фиксируется в **смарт-контракте** — как в неизменяемом распределённом реестре.

Сценарий:

1. Несколько роботов (`R1`, `R2`, `R3`) подключены к MQTT-брокеру.
2. Появляются задания (`T1`, `T2`, `T3`) — «перевезти груз», «посетить точку» и т. п.
3. Каждый робот публикует ставку — насколько ему выгодно взять каждое задание.
4. Координатор собирает ставки и находит назначение, максимизирующее суммарную эффективность.
5. Вычисляется SHA-256 хеш от назначения.
6. Результат (`auctionId`, хеш, победители, задания, время) отправляется в смарт-контракт через API.
7. В смарт-контракте появляется событие `AuctionRegistered`, по которому позже можно проверить, что результат не был изменён.

Смарт-контракт **не участвует в каждом шаге торга** — это было бы слишком дорого и медленно. Он фиксирует только итог. Сам аукцион выполняется вне блокчейна.

## Структура репозитория

```
.
├── src/                          # демонстрационная программа
│   ├── auction.py                # точный аукцион (перебор перестановок)
│   ├── config.py                 # настройки из .env
│   ├── coordinator.py            # собирает ставки, запускает аукцион, регистрирует результат
│   ├── demo.py                   # точка входа: python -m src.demo
│   ├── hashing.py                # канонический SHA-256 от назначения
│   ├── models.py                 # Task, Bid, Assignment, AuctionResult
│   ├── mqtt_client.py            # обёртка над paho-mqtt
│   ├── robot_agent.py            # робот: слушает auction/start, публикует ставки
│   └── smart_contract/
│       ├── interface.py          # ABC
│       ├── stub.py               # локальный JSON-реестр (по умолчанию)
│       ├── http_client.py        # HTTP-клиент к реальному API
│       └── factory.py            # выбор клиента по .env
├── report_NIR.tex                # отчёт по НИР (LaTeX, XeLaTeX)
├── sources.txt                   # список из 10 источников
├── requirements.txt              # Python-зависимости
├── .env.example                  # шаблон конфигурации (без секретов)
├── .gitignore
└── README.md
```

## Требования

- **Python** 3.10+
- **MQTT-брокер** — [mosquitto](https://mosquitto.org/) или любой другой
  - Arch: `sudo pacman -S mosquitto`
  - Ubuntu/Debian: `sudo apt install mosquitto`
  - macOS: `brew install mosquitto`
- **XeLaTeX** (только для сборки отчёта)
  - Arch: `sudo pacman -S texlive-xetex texlive-langcyrillic texlive-latexextra`
  - Ubuntu/Debian: `sudo apt install texlive-xetex texlive-lang-cyrillic texlive-latex-extra`
  - Шрифт **Times New Roman** для корректного вида PDF (без него используется FreeSerif)

## Быстрый старт

```bash
# 1. Клонировать
git clone https://github.com/Avoerfik/mpei-nir-smartcontract-robotics.git
cd mpei-nir-smartcontract-robotics

# 2. Виртуальное окружение и зависимости
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Поднять MQTT-брокер (в отдельном терминале)
mosquitto -v

# 4. Запустить демо
python -m src.demo
```

Ожидаемый вывод в терминале:

```
... [src.robot_agent] [R1] bid T1 = 9.000
... [src.robot_agent] [R2] bid T2 = 8.000
... [src.robot_agent] [R3] bid T3 = 7.500
... [src.coordinator] collected 9/9 bids
... [src.coordinator] auction result:
... [src.coordinator]   R1 -> T1 (value=9.000)
... [src.coordinator]   R2 -> T2 (value=8.000)
... [src.coordinator]   R3 -> T3 (value=7.500)
... [src.coordinator] total_score = 24.500
... [src.coordinator] проверка: оптимум по перебору = 24.500
... [src.coordinator] assignment hash = 0x...
... [src.smart_contract.stub] [STUB] AuctionRegistered, registry size = 1
... [demo] === FINAL ===
```

Запись аукциона сохраняется в `local_registry/auction_registry_stub.json`.

## Смарт-контракт: заглушка и реальный API

По умолчанию используется **заглушка** (`src/smart_contract/stub.py`): она пишет запись в локальный JSON-файл и в лог — этого достаточно для отладки и видео.

Когда появится реальный API от руководителя — программа переключится на `HttpSmartContractClient` автоматически. Для этого скопируйте `.env.example` в `.env` и заполните:

```env
SMART_CONTRACT_API_URL=https://...        # базовый URL API
SMART_CONTRACT_ADDRESS=0x...              # адрес контракта в блокчейне
SMART_CONTRACT_CHAIN_ID=...               # идентификатор сети
SMART_CONTRACT_API_TOKEN=...              # токен авторизации
```

Признак успешного переключения — в логе вместо `[STUB] AuctionRegistered` появится `[HTTP] AuctionRegistered tx=0x...`.

> ⚠️ Файл `.env` содержит секреты и **не должен попадать в git**. Он уже в `.gitignore`.

## Отчёт по НИР

- Исходник: [`report_NIR.tex`](report_NIR.tex)
- Сборка:
  ```bash
  xelatex report_NIR.tex
  xelatex report_NIR.tex   # второй прогон — для содержания и ссылок
  ```
  или `latexmk -xelatex report_NIR.tex`
- Оформлен по требованиям МЭИ (`правила_оформления_doc.pdf`): Times New Roman 14 пт, интервал 1,25, поля 3/1,5/2/2 см, структурные элементы ПРОПИСНЫМИ по центру, разделы — с абзацного отступа, список источников по порядку появления в тексте.

## Список источников

[`sources.txt`](sources.txt) — 10 источников: 8 по распределению задач в многороботных системах (CBAA/CBBA, аукционный алгоритм Берцекаса, алгоритм 3.1 Каляева) и 2 по смарт-контрактам (Ethereum Whitepaper, Solidity docs).

При правке списка синхронизируйте `sources.txt` и блок `\bibitem` в `report_NIR.tex`.

## Видеодемонстрация

20–30-секундная запись работы демо: _ссылка появится после записи_.

## Лицензия

См. [`LICENSE`](LICENSE).
