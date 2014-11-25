#ifndef __lib_gdi_region_h
#define __lib_gdi_region_h

#include <lib/base/object.h>
#include <lib/gdi/erect.h>
#include <vector>

class gRegion
{
private:
	inline void FindBand(
			std::vector<eRect>::const_iterator r,
			std::vector<eRect>::const_iterator &rBandEnd,
			std::vector<eRect>::const_iterator rEnd,
			int &ry1)
	{
		ry1 = r->y1;
		rBandEnd = r+1;
		while ((rBandEnd != rEnd) && (rBandEnd->y1 == ry1))
			rBandEnd++;
	}
	
	inline void AppendRegions(
		std::vector<eRect>::const_iterator r,
		std::vector<eRect>::const_iterator rEnd)
	{
		m_rects.insert(m_rects.end(), r, rEnd);
	}

	int do_coalesce(int prevStart, unsigned int curStart);
	inline void coalesce(int &prevBand, unsigned int curBand)
	{
		if (curBand - prevBand == m_rects.size() - curBand) {
			prevBand = do_coalesce(prevBand, curBand);
		} else {
			prevBand = curBand;
		}
	};
	void appendNonO(std::vector<eRect>::const_iterator r, 
			std::vector<eRect>::const_iterator rEnd, int y1, int y2);

	void intersectO(
			std::vector<eRect>::const_iterator r1,
			std::vector<eRect>::const_iterator r1End,
			std::vector<eRect>::const_iterator r2,
			std::vector<eRect>::const_iterator r2End,
			int y1, int y2);
	void subtractO(
			std::vector<eRect>::const_iterator r1,
			std::vector<eRect>::const_iterator r1End,
			std::vector<eRect>::const_iterator r2,
			std::vector<eRect>::const_iterator r2End,
			int y1, int y2);
	void mergeO(
			std::vector<eRect>::const_iterator r1,
			std::vector<eRect>::const_iterator r1End,
			std::vector<eRect>::const_iterator r2,
			std::vector<eRect>::const_iterator r2End,
			int y1, int y2);
	void regionOp(const gRegion &reg1, const gRegion &reg2, int opcode);

	std::vector<eRect> m_rects;
	eRect m_extends;
public:

	const std::vector<eRect> &rects() const { return m_rects; };
	const eRect &extends() const { return m_extends; }
	
	enum
	{
			// note: bit 0 and bit 1 have special meanings
		OP_INTERSECT = 0,
		OP_SUBTRACT  = 1,
		OP_UNION     = 3
	};
	
	gRegion(const std::vector<eRect> &rects);
	gRegion(const eRect &rect);
	gRegion();

	gRegion operator&(const gRegion &r2) const;
	gRegion operator-(const gRegion &r2) const;
	gRegion operator|(const gRegion &r2) const;
	gRegion &operator&=(const gRegion &r2);
	gRegion &operator-=(const gRegion &r2);
	gRegion &operator|=(const gRegion &r2);
	
	void intersect(const gRegion &r1, const gRegion &r2);
	void subtract(const gRegion &r1, const gRegion &r2);
	void merge(const gRegion &r1, const gRegion &r2);
	
	void moveBy(const ePoint &offset);
	
	bool empty() const { return m_extends.empty(); }
	bool valid() const { return m_extends.valid(); }
	bool isRect() const { return valid() && (m_rects.size() == 1); }
	
	void setEmpty();
	void setRect(const eRect &rect);
	void setRects(const std::vector<eRect> &rects);

	static gRegion invalidRegion() { return gRegion(eRect::invalidRect()); }
	
	void scale(int x_n, int x_d, int y_n, int y_d);
};

inline gRegion::gRegion(const std::vector<eRect> &rects)
{
	setRects(rects);
}

inline gRegion::gRegion(const eRect &rect)
{
	setRect(rect);
}

inline gRegion::gRegion()
{
	setRect(eRect::emptyRect());
}

inline void gRegion::setEmpty()
{
	setRect(eRect::emptyRect());
}

inline gRegion gRegion::operator&(const gRegion &r2) const
{
	gRegion res;
	res.intersect(*this, r2);
	return res;
}

inline gRegion gRegion::operator-(const gRegion &r2) const 
{
	gRegion res;
	res.subtract(*this, r2);
	return res;
}

inline gRegion gRegion::operator|(const gRegion &r2) const
{
	gRegion res;
	res.merge(*this, r2);
	return res;
}

inline gRegion &gRegion::operator&=(const gRegion &r2)
{
	gRegion res;
	res.intersect(*this, r2);
	return *this = res;
}

inline gRegion &gRegion::operator-=(const gRegion &r2)
{
	gRegion res;
	res.subtract(*this, r2);
	return *this = res;
}

inline gRegion &gRegion::operator|=(const gRegion &r2)
{
	gRegion res;
	res.merge(*this, r2);
	return *this = res;
}

#endif
