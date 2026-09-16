import { prisma } from '../../config/database';
import { LedgerType } from '@prisma/client';

export class InventoryService {
  // FR-INV-01 & FR-INV-02: Record Inventory Ledger and calculate Weighted Average Cost (WAC)
  static async createPurchaseReceipt(tenantId: string, data: { branchId: string; skuId: string; importQuantity: number; importUnitPrice: number; referenceId?: string }) {
    if (data.importQuantity <= 0) throw new Error('Quantity must be greater than 0');

    return await prisma.$transaction(async (tx) => {
      // Get current SKU & ledger balance
      const variant = await tx.productVariant.findFirst({
        where: { id: data.skuId, tenantId }
      });
      if (!variant) throw new Error('Product SKU not found');

      // Get latest balance for this SKU in branch
      const lastLedger = await tx.inventoryTransaction.findFirst({
        where: { tenantId, branchId: data.branchId, skuId: data.skuId },
        orderBy: { createdAt: 'desc' }
      });

      const currentBalance = lastLedger ? lastLedger.balanceAfter : 0;
      const newBalance = currentBalance + data.importQuantity;

      // Calculate Weighted Average Cost (WAC)
      const currentCogs = variant.cogs || 0;
      const newCogs = ((currentBalance * currentCogs) + (data.importQuantity * data.importUnitPrice)) / newBalance;

      // Update Variant COGS
      await tx.productVariant.update({
        where: { id: variant.id },
        data: { cogs: newCogs }
      });

      // Append-Only Inventory Ledger
      const ledgerEntry = await tx.inventoryTransaction.create({
        data: {
          tenantId,
          branchId: data.branchId,
          skuId: data.skuId,
          type: LedgerType.IMPORT,
          quantity: data.importQuantity,
          balanceAfter: newBalance,
          referenceId: data.referenceId || 'IMPORT-' + Date.now()
        }
      });

      return { ledgerEntry, updatedCogs: newCogs, currentStock: newBalance };
    });
  }

  static async getLedgerHistory(tenantId: string, skuId?: string) {
    return await prisma.inventoryTransaction.findMany({
      where: {
        tenantId,
        ...(skuId ? { skuId } : {})
      },
      include: { variant: true, branch: true },
      orderBy: { createdAt: 'desc' }
    });
  }
}
