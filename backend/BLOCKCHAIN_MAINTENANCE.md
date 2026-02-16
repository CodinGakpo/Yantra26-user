# Blockchain Maintenance Scripts

This directory contains utility scripts for maintaining the blockchain integration.

## Scripts

### 1. `fund_blockchain_account.py`

**Purpose**: Funds your blockchain account with ETH from Ganache's pre-funded accounts.

**When to use**: When you see the error:
```
insufficient funds for gas * price + value
```

**Usage**:
```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
source venv/bin/activate

# Fund with default amount (10 ETH)
python fund_blockchain_account.py

# Fund with custom amount
python fund_blockchain_account.py 20
```

**What it does**:
- Connects to your Ganache blockchain
- Identifies your working account from `BLOCKCHAIN_PRIVATE_KEY`
- Transfers ETH from a Ganache pre-funded account to your working account
- Displays balances before and after

---

### 2. `cleanup_blockchain_db.py`

**Purpose**: Cleans up duplicate or failed blockchain transactions in the database.

**When to use**: When you see database errors like:
```
UNIQUE constraint failed: blockchain_blockchaintransaction.tx_hash
```

**Usage**:
```bash
# Check what would be cleaned (dry run)
python cleanup_blockchain_db.py

# Actually perform the cleanup
python cleanup_blockchain_db.py --fix
```

**What it does**:
- Finds and removes duplicate transaction hashes
- Removes failed transactions
- Resets old pending transactions (>5 minutes old)
- Displays database statistics

---

## Common Issues and Solutions

### Issue 1: Insufficient funds for gas

**Error Message**:
```
Error: insufficient funds for gas * price + value
```

**Solution**:
```bash
python fund_blockchain_account.py
```

This transfers 10 ETH from a Ganache account to your working account.

---

### Issue 2: Duplicate transaction hash

**Error Message**:
```
UNIQUE constraint failed: blockchain_blockchaintransaction.tx_hash
```

**Solution**:
```bash
python cleanup_blockchain_db.py --fix
```

This removes failed/duplicate transactions from the database.

---

### Issue 3: Ganache connection issues

**Error Message**:
```
Cannot connect to blockchain node
```

**Solution**:
1. Make sure Ganache is running
2. Check that `BLOCKCHAIN_NODE_URL` in settings points to the correct address
   - Default: `http://localhost:7545` (Ganache GUI)
   - Alternative: `http://localhost:8545` (Ganache CLI)

---

## Configuration

### Environment Variables

The scripts use these settings from your Django configuration:

- `BLOCKCHAIN_NODE_URL`: Ganache connection URL (default: `http://127.0.0.1:7545`)
- `BLOCKCHAIN_PRIVATE_KEY`: Private key of your working account
- `BLOCKCHAIN_GAS_LIMIT`: Gas limit for transactions (default: 500000)
- `BLOCKCHAIN_TX_TIMEOUT`: Transaction timeout in seconds (default: 120)

### Checking Your Configuration

You can verify your blockchain settings with:

```bash
python manage.py shell
>>> from django.conf import settings
>>> print(settings.BLOCKCHAIN_NODE_URL)
>>> print(settings.BLOCKCHAIN_ENABLED)
```

---

## Quick Start After Fresh Ganache Reset

If you reset Ganache or start fresh:

1. **Fund your account**:
   ```bash
   python fund_blockchain_account.py
   ```

2. **Clean database** (if migrating from old Ganache):
   ```bash
   python cleanup_blockchain_db.py --fix
   ```

3. **Run migrations** (if needed):
   ```bash
   python manage.py migrate
   ```

4. **Start server**:
   ```bash
   python manage.py runserver
   ```

---

## Troubleshooting

### Script can't find Django modules

**Solution**: Make sure you activated the virtual environment:
```bash
source venv/bin/activate
```

### Script can't connect to database

**Solution**: Make sure you're in the `backend` directory:
```bash
cd backend
```

### Ganache accounts all depleted

If all Ganache accounts run out of funds:
1. Close Ganache
2. Delete the workspace or create a new one
3. Reopen Ganache (fresh accounts with 100 ETH each)
4. Run `fund_blockchain_account.py` again

---

## Regular Maintenance

### Daily Development

Before starting work each day:
```bash
# Check blockchain account balance
python fund_blockchain_account.py

# Clean up any failed transactions
python cleanup_blockchain_db.py --fix
```

### Weekly

```bash
# Full database statistics review
python cleanup_blockchain_db.py
```

---

## Need Help?

If you encounter issues not covered here:

1. Check Django logs for detailed error messages
2. Run the cleanup script to see database statistics
3. Verify Ganache is running and accessible
4. Check that your private key is correctly configured

---

## Technical Details

### How Ganache Works

- Ganache provides 10 pre-funded accounts with 100 ETH each
- Each transaction costs gas (paid in ETH)
- Your working account needs ETH to pay for gas fees
- When out of ETH, transactions fail with "insufficient funds" error

### Transaction Lifecycle

1. **Create transaction** → Status: PENDING
2. **Send to blockchain** → Transaction hash generated
3. **Wait for confirmation** → Mining
4. **Confirmed** → Status: CONFIRMED (or FAILED)

### Database Cleanup

The cleanup script:
- Removes duplicates (keeps most recent)
- Deletes failed transactions (can be retried)
- Resets stale pending transactions (>5 minutes old)
- Maintains data integrity
