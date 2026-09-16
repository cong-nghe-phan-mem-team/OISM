import { prisma } from '../../config/database';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';

export class AuthService {
  static async registerTenant(data: { tenantName: string; ownerEmail: string; password: string; fullName: string; phone?: string }) {
    const existingUser = await prisma.user.findUnique({ where: { email: data.ownerEmail } });
    if (existingUser) throw new Error('Email already exists');

    const hashedPassword = await bcrypt.hash(data.password, 10);

    return await prisma.$transaction(async (tx) => {
      const tenant = await tx.tenant.create({
        data: { name: data.tenantName }
      });

      const owner = await tx.user.create({
        data: {
          tenantId: tenant.id,
          email: data.ownerEmail,
          passwordHash: hashedPassword,
          fullName: data.fullName,
          phone: data.phone,
          role: 'OWNER'
        }
      });

      const defaultBranch = await tx.branch.create({
        data: {
          tenantId: tenant.id,
          name: 'Kho/Chi nhánh chính',
          code: 'MAIN'
        }
      });

      return { tenant, owner, defaultBranch };
    });
  }

  static async login(email: string, password: string) {
    const user = await prisma.user.findUnique({ where: { email } });
    if (!user) throw new Error('Invalid email or password');

    const isMatch = await bcrypt.compare(password, user.passwordHash);
    if (!isMatch) throw new Error('Invalid email or password');

    const token = jwt.sign(
      { userId: user.id, tenantId: user.tenantId, role: user.role },
      process.env.JWT_SECRET || 'secret',
      { expiresIn: '1d' }
    );

    return {
      token,
      user: { id: user.id, email: user.email, fullName: user.fullName, role: user.role, tenantId: user.tenantId }
    };
  }
}
