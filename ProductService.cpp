import { prisma } from '../../config/database';

export class ProductService {
  static async createProduct(tenantId: string, data: { title: string; categoryId?: string; brandId?: string; variants: Array<{ sku: string; barcode?: string; retailPrice: number; wholesalePrice?: number; attributes?: any }> }) {
    return await prisma.$transaction(async (tx) => {
      const product = await tx.product.create({
        data: {
          tenantId,
          title: data.title,
          categoryId: data.categoryId,
          brandId: data.brandId,
        }
      });

      const variantsData = data.variants.map((v) => ({
        tenantId,
        productId: product.id,
        sku: v.sku,
        barcode: v.barcode,
        retailPrice: v.retailPrice,
        wholesalePrice: v.wholesalePrice || 0,
        attributes: v.attributes || {}
      }));

      await tx.productVariant.createMany({ data: variantsData });

      return tx.product.findUnique({
        where: { id: product.id },
        include: { variants: true, category: true, brand: true }
      });
    });
  }

  static async getProducts(tenantId: string) {
    return await prisma.product.findMany({
      where: { tenantId },
      include: { variants: true, category: true, brand: true }
    });
  }
}
